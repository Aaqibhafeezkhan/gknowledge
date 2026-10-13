#!/bin/sh
# Build a plain .deb (no debhelper needed) from the source tree.
# Usage: build-aux/deb/build-deb.sh [output-dir]
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${1:-$ROOT/dist}
VERSION=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT/gknowledge/__init__.py")
PKG=$(mktemp -d)
trap 'rm -rf "$PKG"' EXIT

make -C "$ROOT" install DESTDIR="$PKG" PREFIX=/usr PYTHON=/usr/bin/python3 >/dev/null
# The Makefile's cache refresh helpers are not meaningful inside DESTDIR.
find "$PKG" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

mkdir -p "$PKG/DEBIAN" "$OUT"
SIZE=$(du -sk "$PKG/usr" | cut -f1)
cat > "$PKG/DEBIAN/control" <<CTRL
Package: gknowledge
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1
Recommends: python3-pypdf
Installed-Size: $SIZE
Maintainer: gknowledge contributors <noreply@users.noreply.github.com>
Homepage: https://github.com/openapi/gknowledge
Description: Native GNOME knowledge workstation
 Turns documents, notes and links into an evolving, inspectable
 Markdown knowledge base with provenance and citations. Works fully
 offline with a built-in heuristic engine; OpenAI-compatible endpoints
 such as Ollama are optional.
CTRL
dpkg-deb --root-owner-group --build "$PKG" "$OUT/gknowledge_${VERSION}_all.deb"
echo "Built $OUT/gknowledge_${VERSION}_all.deb"
