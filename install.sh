#!/usr/bin/env bash
# gknowledge installer.
#
#   curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
#
# Ubuntu / Debian: downloads the latest .deb and installs it with apt, which
# also pulls GTK 4, Libadwaita and PyGObject.
# Other distributions: installs the latest release into ~/.local (no root),
# after checking that PyGObject, GTK 4 and Libadwaita are present.
#
# Environment overrides:
#   GKNOWLEDGE_REPO   owner/repo (default openapi/gknowledge)
#   GKNOWLEDGE_MODE   deb | local (default: deb when apt is available)
set -euo pipefail

REPO="${GKNOWLEDGE_REPO:-openapi/gknowledge}"
BASE="https://github.com/${REPO}/releases/latest/download"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "'$1' is required but not installed."; }

sudo_cmd() {
  if [ "$(id -u)" -eq 0 ]; then "$@"; else need sudo; sudo "$@"; fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

install_deb() {
  info "Downloading the latest gknowledge .deb"
  curl -fL --progress-bar -o "$TMP/gknowledge_all.deb" "$BASE/gknowledge_all.deb" \
    || die "Download failed from $BASE/gknowledge_all.deb"
  # apt downloads as the unprivileged _apt user, which cannot enter mktemp's 0700 dir.
  chmod 755 "$TMP"
  chmod 644 "$TMP/gknowledge_all.deb"
  info "Installing with apt (you may be asked for your password)"
  sudo_cmd apt-get install -y "$TMP/gknowledge_all.deb"
  if [ -e "$HOME/.local/bin/gknowledge" ] || [ -e "$HOME/.local/share/applications/io.gknowledge.Gknowledge.desktop" ]; then
    warn "An older gknowledge in ~/.local shadows this install (old icon and version)."
    warn "Remove it with: rm -rf ~/.local/bin/gknowledge ~/.local/bin/gknowledge-mcp ~/.local/share/gknowledge ~/.local/share/applications/io.gknowledge.Gknowledge.desktop ~/.local/share/icons/hicolor/scalable/apps/io.gknowledge.Gknowledge.svg ~/.local/share/metainfo/io.gknowledge.Gknowledge.metainfo.xml && gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor"
  fi
  info "Done. Launch gknowledge from the app grid or run: gknowledge"
}

install_local() {
  need python3
  need make
  need tar
  python3 - <<'PY' || die "Missing PyGObject, GTK 4 or Libadwaita. Install them with your package manager (Fedora: python3-gobject gtk4 libadwaita; Arch: python-gobject gtk4 libadwaita) and run this again."
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: F401
PY
  info "Resolving the latest release"
  tag="$(curl -fsSLI -o /dev/null -w '%{url_effective}' "https://github.com/${REPO}/releases/latest")"
  tag="${tag##*/}"
  if [ -z "$tag" ] || [ "$tag" = "latest" ]; then
    die "Could not determine the latest release."
  fi
  info "Downloading gknowledge ${tag}"
  curl -fsSL "https://github.com/${REPO}/archive/refs/tags/${tag}.tar.gz" | tar -xz -C "$TMP"
  src="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -n1)"
  info "Installing into ~/.local"
  make -C "$src" install PREFIX="$HOME/.local" >/dev/null
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) warn "Add ~/.local/bin to your PATH to run 'gknowledge' from a terminal." ;;
  esac
  info "Done. Launch gknowledge from the app grid or run: gknowledge"
}

main() {
  need curl
  [ "$(uname -s)" = "Linux" ] || die "gknowledge is a Linux desktop application."
  mode="${GKNOWLEDGE_MODE:-}"
  if [ -z "$mode" ]; then
    if command -v apt-get >/dev/null 2>&1 && command -v dpkg >/dev/null 2>&1; then
      mode=deb
    else
      mode=local
    fi
  fi
  case "$mode" in
    deb) install_deb ;;
    local) install_local ;;
    *) die "Unknown GKNOWLEDGE_MODE '$mode' (use deb or local)." ;;
  esac
}

main "$@"
