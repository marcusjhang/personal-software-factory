#!/usr/bin/env sh
# Personal Software Factory installer.
#
#   curl -fsSL https://raw.githubusercontent.com/marcusjhang/personal-software-factory/main/install.sh | sh
#
# Installs the `psf` command using the first available tool (pipx > uv > pip),
# then tells you how to scaffold a factory in any repository.
set -eu

REPO="${PSF_REPO:-https://github.com/marcusjhang/personal-software-factory}"
SPEC="git+${REPO}"

echo "Installing Personal Software Factory from ${REPO} ..."

if command -v pipx >/dev/null 2>&1; then
  pipx install --force "${SPEC}"
elif command -v uv >/dev/null 2>&1; then
  uv tool install --force "${SPEC}"
elif command -v pip3 >/dev/null 2>&1; then
  pip3 install --user --force-reinstall "${SPEC}"
else
  echo "error: need one of pipx, uv, or pip3 on PATH" >&2
  exit 1
fi

echo
echo "Installed. Next, in any GitHub repository:"
echo "  psf init"
echo "  psf validate"
echo "  psf run \"<your goal>\""
echo "  psf audit"
