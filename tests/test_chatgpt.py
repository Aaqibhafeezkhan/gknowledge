"""ChatGPT plan provider against fake OAuth and Responses servers (no network)."""

from __future__ import annotations

import base64
import http.server
import json
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from gknowledge.providers.base import LLMMessage, ProviderError
from gknowledge.providers.chatgpt import (
    AccountStore, ChatGPTAuth, ChatGPTPlanProvider, SignInError)


def _jwt(claims: dict) -> str:
    enc = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    return f"{enc({'alg': 'none'})}.{enc(claims)}."


class FakeOpenAI:
    """One server standing in for auth.openai.com and api.openai.com."""

    def __init__(self, scope="openid offline_access chatgpt.tokens.use.direct",
                 responses_status=200, responses_body=""):
        self.scope = scope
        self.responses_status = responses_status
        self.responses_body = responses_body
        self.nonce = ""
        self.token_requests: list[dict] = []
        self.response_payloads: list[dict] = []
        self.issued_client = "oaiapp_test123"
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def _send(self, code, body, ctype="application/json"):
                data = body.encode() if isinstance(body, str) else body
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(n).decode()
                if self.path == "/token":
                    form = {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}
                    outer.token_requests.append(form)
                    claims = {"aud": form["client_id"], "exp": time.time() + 3600,
                              "nonce": outer.nonce, "email": "ada@example.com",
                              "sub": "user-1"}
                    self._send(200, json.dumps({
                        "access_token": f"at-{len(outer.token_requests)}",
                        "refresh_token": "rt-1", "id_token": _jwt(claims),
                        "expires_in": 3600, "scope": outer.scope}))
                elif self.path == "/v1/responses":
                    outer.response_payloads.append(json.loads(raw))
                    self._send(outer.responses_status, outer.responses_body,
                               "text/event-stream")
                else:
                    self._send(404, "{}")

            def do_GET(self):  # noqa: N802
                if self.path == "/v1/models":
                    self._send(200, json.dumps({"data": [{"id": "gpt-test"}]}))
                else:
                    self._send(404, "{}")

            def log_message(self, *_a):
                pass

        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


def _auth(tmp_path, fake):
    return ChatGPTAuth(AccountStore(tmp_path / "chatgpt.json"),
                       authorize_url=f"{fake.base}/authorize",
                       token_url=f"{fake.base}/token",
                       discovery_url=f"{fake.base}/discovery", port=0)


def _browser(fake, *, error=None):
    """A 'browser' that follows the authorize URL straight to the callback."""
    def open_url(url):
        q = {k: v[0] for k, v in urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query).items()}
        fake.nonce = q["nonce"]
        assert q["code_challenge_method"] == "S256"
        assert q["scope"].split()[-1] == "chatgpt.tokens.use.direct"
        assert q["redirect_uri"].startswith("http://127.0.0.1:")
        cb = {"state": q["state"]}
        if error:
            cb["error"] = error
        else:
            cb.update(code="abc", client_id=fake.issued_client)
        target = f"{q['redirect_uri']}?{urllib.parse.urlencode(cb)}"
        threading.Thread(target=lambda: urllib.request.urlopen(target).read(),
                         daemon=True).start()
        open_url.params = q
    return open_url


def test_sign_in_registers_and_grants_sharing(tmp_path):
    fake = FakeOpenAI()
    try:
        auth = _auth(tmp_path, fake)
        browser = _browser(fake)
        acct = auth.sign_in(browser, timeout=10)
        assert browser.params["client_id"] == "dynamic_agent_client"
        assert browser.params["agent_name_hint"] == "gknowledge"
        assert acct.host_id.startswith("urn:uuid:")
        assert acct.client_id == "oaiapp_test123"
        assert acct.email == "ada@example.com"
        assert acct.sharing and acct.token_fresh()
        assert (tmp_path / "chatgpt.json").stat().st_mode & 0o777 == 0o600
        assert fake.token_requests[0]["code_verifier"]
        # Second sign-in reuses the issued client id and omits the name hint.
        browser2 = _browser(fake)
        auth.sign_in(browser2, timeout=10)
        assert browser2.params["client_id"] == "oaiapp_test123"
        assert "agent_name_hint" not in browser2.params
    finally:
        fake.close()


def test_declined_sign_in(tmp_path):
    fake = FakeOpenAI()
    try:
        with pytest.raises(SignInError, match="declined"):
            _auth(tmp_path, fake).sign_in(_browser(fake, error="access_denied"), timeout=10)
    finally:
        fake.close()


def test_signed_in_without_spend_scope_is_not_sharing(tmp_path):
    fake = FakeOpenAI(scope="openid offline_access")
    try:
        auth = _auth(tmp_path, fake)
        acct = auth.sign_in(_browser(fake), timeout=10)
        assert acct.signed_in and not acct.sharing
        with pytest.raises(ProviderError, match="not granted"):
            auth.valid_account()
    finally:
        fake.close()


SSE = ("event: response.output_text.delta\n"
       'data: {"type":"response.output_text.delta","delta":"Hello "}\n\n'
       'data: {"type":"response.output_text.delta","delta":"chess"}\n\n'
       'data: {"type":"response.completed","response":{"usage":'
       '{"input_tokens":7,"output_tokens":2}}}\n\n')


def test_provider_streams_with_plan_rules(tmp_path):
    fake = FakeOpenAI(responses_body=SSE)
    try:
        auth = _auth(tmp_path, fake)
        auth.sign_in(_browser(fake), timeout=10)
        prov = ChatGPTPlanProvider("gpt-test", auth=auth, api_base=f"{fake.base}/v1")
        assert prov.available()
        res = prov.complete([LLMMessage("system", "Be brief."),
                             LLMMessage("user", "Say hi")], json_object=True)
        assert res.content == "Hello chess"
        assert (res.prompt_tokens, res.completion_tokens) == (7, 2)
        p = fake.response_payloads[0]
        assert p["stream"] is True and p["store"] is False
        assert "temperature" not in p and "max_output_tokens" not in p
        assert all(i["role"] != "system" for i in p["input"])
        assert "Be brief." in p["instructions"] and "JSON" in p["instructions"]
    finally:
        fake.close()


def test_usage_limit_is_reported(tmp_path):
    fake = FakeOpenAI(responses_status=429,
                      responses_body='{"error":{"code":"subscription_sharing_usage_limit_exceeded"}}')
    try:
        auth = _auth(tmp_path, fake)
        auth.sign_in(_browser(fake), timeout=10)
        prov = ChatGPTPlanProvider("gpt-test", auth=auth, api_base=f"{fake.base}/v1")
        with pytest.raises(ProviderError, match="plan limit reached"):
            prov.complete([LLMMessage("user", "hi")])
    finally:
        fake.close()


def test_sign_out_clears_tokens_but_keeps_host_id(tmp_path):
    fake = FakeOpenAI()
    try:
        auth = _auth(tmp_path, fake)
        acct = auth.sign_in(_browser(fake), timeout=10)
        host = acct.host_id
        auth.sign_out()
        after = auth.store.load()
        assert not after.signed_in and after.host_id == host
    finally:
        fake.close()
