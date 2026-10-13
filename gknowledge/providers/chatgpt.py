"""ChatGPT plan provider: "Sign in with ChatGPT" for local, open-source apps.

The user signs in with their own ChatGPT account (OAuth 2.0 authorization code
with PKCE and a loopback redirect, like linking a cloud drive). Model calls are
then made through the Responses API and are charged to the user's plan, not to
the app author. No API key is involved.

Reference: https://developers.openai.com/siwc/token-sharing-open-source/sign-in
Stdlib only. All network endpoints are parameters so tests can fake them.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from .base import LLMMessage, LLMProvider, LLMResponse, ProviderError

AUTH_BASE = "https://auth.openai.com"
AUTHORIZE_URL = f"{AUTH_BASE}/api/accounts/authorize"
TOKEN_URL = f"{AUTH_BASE}/api/accounts/oauth/token"
DISCOVERY_URL = f"{AUTH_BASE}/.well-known/openid-configuration"
API_BASE = "https://api.openai.com/v1"

REGISTRATION_CLIENT_ID = "dynamic_agent_client"
SPEND_SCOPE = "chatgpt.tokens.use.direct"
SCOPES = ["openid", "profile", "email", "offline_access", "resource.invoke", SPEND_SCOPE]
DEFAULT_PORT = 1455
CALLBACK_PATH = "/auth/callback"
APP_NAME_HINT = "gknowledge"


class SignInError(ProviderError):
    """The sign-in flow failed or was cancelled."""


# -- account storage ---------------------------------------------------------
@dataclass
class ChatGPTAccount:
    """Everything we keep about the signed-in user (app-wide, not per project)."""

    host_id: str = ""
    client_id: str = ""
    access_token: str = ""
    refresh_token: str = ""
    id_token: str = ""
    scope: str = ""
    expires_at: float = 0.0
    email: str = ""
    sub: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def signed_in(self) -> bool:
        return bool(self.client_id and self.refresh_token)

    @property
    def sharing(self) -> bool:
        """Signed in *and* allowed to spend plan usage."""
        return self.signed_in and SPEND_SCOPE in self.scope.split()

    def token_fresh(self, skew: float = 60.0) -> bool:
        return bool(self.access_token) and time.time() < self.expires_at - skew


def default_account_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    d = Path(base) / "gknowledge"
    d.mkdir(parents=True, exist_ok=True)
    return d / "chatgpt.json"


class AccountStore:
    """JSON file with 0600 permissions, written atomically."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else default_account_path()

    def load(self) -> ChatGPTAccount:
        try:
            data = json.loads(self.path.read_text("utf-8"))
            known = {k: data[k] for k in asdict(ChatGPTAccount()) if k in data}
            acct = ChatGPTAccount(**known)
        except (OSError, ValueError, TypeError):
            acct = ChatGPTAccount()
        if not acct.host_id:                       # stable per installation
            acct.host_id = f"urn:uuid:{uuid.uuid4()}"
            self.save(acct)
        return acct

    def save(self, acct: ChatGPTAccount) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(asdict(acct), fh, indent=2)
        os.replace(tmp, self.path)

    def clear_tokens(self) -> ChatGPTAccount:
        acct = self.load()
        keep = ChatGPTAccount(host_id=acct.host_id, client_id=acct.client_id)
        self.save(keep)
        return keep


# -- helpers -------------------------------------------------------------------
def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def new_pkce() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(48))
    return verifier, _b64url(hashlib.sha256(verifier.encode("ascii")).digest())


def decode_jwt_claims(token: str) -> dict:
    """Decode (without verifying) the payload of a JWT.

    The ID token is received directly from the token endpoint over TLS, which
    OpenID Connect Core 3.1.3.7 accepts in place of a signature check; we still
    validate audience, expiry and nonce.
    """
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception as exc:  # noqa: BLE001
        raise SignInError(f"Invalid ID token: {exc}") from exc


def _http_json(url: str, *, data: dict | None = None, headers: dict | None = None,
               timeout: float = 30.0) -> dict:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers or {})
    if data is not None:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise SignInError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SignInError(f"Connection failed: {exc.reason}") from exc


# -- loopback callback -----------------------------------------------------------
class _CallbackServer:
    def __init__(self, port: int = DEFAULT_PORT):
        self.result: dict | None = None
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path != CALLBACK_PATH:
                    self.send_error(404)
                    return
                outer.result = {k: v[0] for k, v in
                                urllib.parse.parse_qs(parsed.query).items()}
                page = ("<html><body style='font-family:sans-serif;text-align:center;"
                        "margin-top:4em'><h2>gknowledge is connected</h2>"
                        "<p>You can close this tab and go back to the app.</p>"
                        "</body></html>").encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)

            def log_message(self, *_a):  # silence
                pass

        try:
            self.httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
        except OSError:
            self.httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.timeout = 0.5
        self.port = self.httpd.server_address[1]
        self.redirect_uri = f"http://127.0.0.1:{self.port}{CALLBACK_PATH}"

    def wait(self, timeout: float, cancel: threading.Event | None) -> dict:
        deadline = time.time() + timeout
        while self.result is None:
            if cancel is not None and cancel.is_set():
                raise SignInError("Sign-in cancelled.")
            if time.time() > deadline:
                raise SignInError("Sign-in timed out. Please try again.")
            self.httpd.handle_request()
        return self.result

    def close(self):
        self.httpd.server_close()


# -- the OAuth flow ----------------------------------------------------------------
class ChatGPTAuth:
    def __init__(self, store: AccountStore | None = None, *,
                 authorize_url: str = AUTHORIZE_URL, token_url: str = TOKEN_URL,
                 discovery_url: str = DISCOVERY_URL, port: int = DEFAULT_PORT):
        self.store = store or AccountStore()
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.discovery_url = discovery_url
        self.port = port

    # sign in -------------------------------------------------------------
    def sign_in(self, open_url: Callable[[str], None] | None = None, *,
                timeout: float = 300.0,
                cancel: threading.Event | None = None) -> ChatGPTAccount:
        """Run the browser flow. Blocks until done; call it from a worker thread."""
        acct = self.store.load()
        server = _CallbackServer(self.port)
        try:
            verifier, challenge = new_pkce()
            state, nonce = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
            first_time = not acct.client_id
            params = {
                "response_type": "code",
                "client_id": REGISTRATION_CLIENT_ID if first_time else acct.client_id,
                "redirect_uri": server.redirect_uri,
                "scope": " ".join(SCOPES),
                "resource": API_BASE,
                "state": state,
                "nonce": nonce,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "ext_agent_host_id": acct.host_id,
            }
            if first_time:
                params["agent_name_hint"] = APP_NAME_HINT
            elif acct.id_token:
                params["id_token_hint"] = acct.id_token
            if acct.email and not first_time:
                params["login_hint"] = acct.email
            url = f"{self.authorize_url}?{urllib.parse.urlencode(params)}"
            (open_url or webbrowser.open)(url)

            cb = server.wait(timeout, cancel)
        finally:
            server.close()

        if cb.get("state") != state:
            raise SignInError("Sign-in response did not match the request.")
        if cb.get("error"):
            if cb["error"] == "access_denied":
                raise SignInError("Sign-in was declined.")
            raise SignInError(f"Sign-in failed: {cb['error']}")
        code = cb.get("code")
        if not code:
            raise SignInError("Sign-in response had no authorization code.")
        client_id = cb.get("client_id") or acct.client_id
        if first_time and not cb.get("client_id"):
            raise SignInError("Registration incomplete: no client id returned.")
        if not first_time and cb.get("client_id") and cb["client_id"] != acct.client_id:
            raise SignInError("Unexpected client id in the sign-in response.")
        # Save the issued client id before exchanging the code.
        acct.client_id = client_id
        self.store.save(acct)

        tok = _http_json(self.token_url, data={
            "grant_type": "authorization_code", "client_id": client_id,
            "code": code, "code_verifier": verifier,
            "redirect_uri": server.redirect_uri, "resource": API_BASE})
        self._apply_tokens(acct, tok, expected_nonce=nonce)
        self.store.save(acct)
        return acct

    def _apply_tokens(self, acct: ChatGPTAccount, tok: dict, *,
                      expected_nonce: str | None = None) -> None:
        if "access_token" not in tok:
            raise SignInError("Token response had no access token.")
        id_token = tok.get("id_token") or acct.id_token
        if tok.get("id_token"):
            claims = decode_jwt_claims(tok["id_token"])
            aud = claims.get("aud")
            auds = aud if isinstance(aud, list) else [aud]
            if acct.client_id not in auds:
                raise SignInError("ID token audience mismatch.")
            if claims.get("exp") and claims["exp"] < time.time() - 60:
                raise SignInError("ID token already expired.")
            if expected_nonce and claims.get("nonce") != expected_nonce:
                raise SignInError("ID token nonce mismatch.")
            acct.email = claims.get("email", acct.email)
            acct.sub = claims.get("sub", acct.sub)
        acct.id_token = id_token
        acct.access_token = tok["access_token"]
        acct.refresh_token = tok.get("refresh_token", acct.refresh_token)
        acct.scope = tok.get("scope", acct.scope)
        acct.expires_at = time.time() + float(tok.get("expires_in", 3600))

    # refresh / sign out --------------------------------------------------------
    def refresh(self) -> ChatGPTAccount:
        acct = self.store.load()
        if not acct.refresh_token:
            raise SignInError("Not signed in.")
        try:
            tok = _http_json(self.token_url, data={
                "grant_type": "refresh_token", "refresh_token": acct.refresh_token,
                "client_id": acct.client_id, "resource": API_BASE})
        except SignInError as exc:
            # Disconnected from ChatGPT settings or expired: drop local tokens.
            self.store.clear_tokens()
            raise SignInError(
                "ChatGPT access was revoked or expired. Please sign in again.") from exc
        self._apply_tokens(acct, tok)
        self.store.save(acct)
        return acct

    def sign_out(self) -> None:
        acct = self.store.load()
        if acct.refresh_token:
            try:
                disc = _http_json(self.discovery_url, timeout=10)
                endpoint = disc.get("revocation_endpoint")
                if endpoint:
                    _http_json(endpoint, data={
                        "token": acct.refresh_token,
                        "token_type_hint": "refresh_token",
                        "client_id": acct.client_id}, timeout=10)
            except SignInError:
                pass                                   # best effort
        self.store.clear_tokens()

    def valid_account(self) -> ChatGPTAccount:
        """Account with a fresh access token, refreshing when needed."""
        acct = self.store.load()
        if not acct.signed_in:
            raise ProviderError("Not signed in to ChatGPT. Open Preferences to sign in.")
        if not acct.token_fresh():
            acct = self.refresh()
        if not acct.sharing:
            raise ProviderError(
                "Signed in, but ChatGPT plan usage was not granted. "
                "Sign in again and allow usage.")
        return acct


# -- the provider ----------------------------------------------------------------------
class ChatGPTPlanProvider(LLMProvider):
    kind = "llm"

    def __init__(self, model: str = "", *, auth: ChatGPTAuth | None = None,
                 api_base: str = API_BASE):
        self.auth = auth or ChatGPTAuth()
        self.api_base = api_base.rstrip("/")
        self.configured_model = model
        self._model: str | None = None
        self.name = "ChatGPT plan"

    def available(self) -> bool:
        return self.auth.store.load().sharing

    # -- model resolution --------------------------------------------------------------
    def list_models(self) -> list[dict]:
        """Models available to the signed-in account, best first.

        The endpoint returns ``{"models": [{slug, display_name, visibility,
        priority, ...}]}``; only ``visibility == "list"`` entries are shown.
        """
        acct = self.auth.valid_account()
        data = _http_json(f"{self.api_base}/models",
                          headers={"Authorization": f"Bearer {acct.access_token}"},
                          timeout=20)
        models = [m for m in data.get("models", [])
                  if m.get("visibility", "list") == "list" and m.get("slug")]
        if not models:                                   # OpenAI-style fallback
            models = [{"slug": m["id"], "display_name": m["id"]}
                      for m in data.get("data", []) if m.get("id")]
        return sorted(models, key=lambda m: m.get("priority", 999))

    def _resolve_model(self, token: str) -> str:
        if self._model:
            return self._model
        try:
            slugs = [m["slug"] for m in self.list_models()]
        except (ProviderError, KeyError):
            slugs = []
        if self.configured_model and (not slugs or self.configured_model in slugs):
            self._model = self.configured_model
        elif slugs:
            self._model = slugs[0]
        else:
            raise ProviderError("No ChatGPT models are available for this account.")
        self.name = f"ChatGPT plan ({self._model})"
        return self._model

    # -- completion ----------------------------------------------------------------------
    def complete(self, messages: list[LLMMessage], *, json_object: bool = False,
                 temperature: float = 0.2, max_tokens: int | None = None) -> LLMResponse:
        # Plan usage rejects explicit system items, temperature and
        # max_output_tokens: system text goes in `instructions`.
        acct = self.auth.valid_account()
        instructions = "\n\n".join(m.content for m in messages if m.role == "system")
        if json_object:
            instructions += "\n\nRespond with a single valid JSON object and nothing else."
        items = []
        for m in messages:
            if m.role == "system":
                continue
            ctype = "output_text" if m.role == "assistant" else "input_text"
            items.append({"role": m.role,
                          "content": [{"type": ctype, "text": m.content}]})
        payload = {"model": self._resolve_model(acct.access_token),
                   "instructions": instructions.strip() or "You are a helpful assistant.",
                   "input": items, "store": False, "stream": True}

        for attempt in (0, 1):
            try:
                return self._stream(payload, acct.access_token)
            except _Unauthorized:
                if attempt:
                    raise ProviderError("ChatGPT rejected the access token.")
                acct = self.auth.refresh()
        raise ProviderError("Unreachable")  # pragma: no cover

    def _stream(self, payload: dict, token: str) -> LLMResponse:
        req = urllib.request.Request(
            f"{self.api_base}/responses", data=json.dumps(payload).encode(),
            method="POST", headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json", "Accept": "text/event-stream"})
        chunks: list[str] = []
        usage: dict = {}
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                for raw in resp:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    body = line[5:].strip()
                    if not body or body == "[DONE]":
                        continue
                    try:
                        ev = json.loads(body)
                    except ValueError:
                        continue
                    et = ev.get("type", "")
                    if et == "response.output_text.delta":
                        chunks.append(ev.get("delta", ""))
                    elif et == "response.completed":
                        usage = (ev.get("response") or {}).get("usage") or {}
                    elif et == "response.incomplete":
                        reason = ((ev.get("response") or {}).get("incomplete_details")
                                  or {}).get("reason", "unknown")
                        raise ProviderError(f"ChatGPT returned an incomplete answer ({reason}).")
                    elif et in ("response.failed", "error"):
                        if "subscription_sharing_usage" in body:
                            raise ProviderError(
                                "ChatGPT plan usage is exhausted or unavailable right now "
                                "(ChatGPT Settings > Usage).")
                        msg = (ev.get("error") or ev.get("response", {}).get("error")
                               or ev)
                        raise ProviderError(f"ChatGPT request failed: {msg}")
        except urllib.error.HTTPError as exc:
            self._raise_http(exc)
        except urllib.error.URLError as exc:
            raise ProviderError(f"Connection failed: {exc.reason}") from exc
        return LLMResponse(content="".join(chunks), model=payload["model"],
                           prompt_tokens=usage.get("input_tokens", 0),
                           completion_tokens=usage.get("output_tokens", 0))

    @staticmethod
    def _raise_http(exc: urllib.error.HTTPError):
        body = exc.read().decode("utf-8", "replace")
        if exc.code == 401:
            raise _Unauthorized()
        if exc.code == 429 and "subscription_sharing_usage_limit_exceeded" in body:
            raise ProviderError(
                "ChatGPT plan limit reached. Raise the app cap or wait for the "
                "window to reset (ChatGPT Settings > Usage).")
        if exc.code == 403 and "subscription_sharing_user_not_eligible" in body:
            raise ProviderError(
                "This ChatGPT account or workspace cannot share plan usage "
                "(Plus or Pro personal plans only).")
        raise ProviderError(f"HTTP {exc.code}: {body[:300]}")


class _Unauthorized(Exception):
    pass
