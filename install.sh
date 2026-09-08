#!/usr/bin/env sh
set -eu

REPO_URL="https://github.com/Tunglam0605/engineering-agent-stack.git"
REF="${EAS_REF:-main}"
if [ "$REF" != "main" ]; then
  echo "EAS v0.3 bootstrap supports only the main branch; version pinning is planned for a later release." >&2
  exit 2
fi
CODEX_HOME="${HOME}/.codex"
CHECKOUT="${CODEX_HOME}/engineering-agent-stack"
VENV_DIR="${CHECKOUT}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"
BIN_DIR="${HOME}/.local/bin"

find_python() {
  for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1 && "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)' >/dev/null 2>&1; then
      printf '%s\n' "$cmd"
      return 0
    fi
  done
  return 1
}

ensure_runtime() {
  if [ ! -x "$VENV_PYTHON" ]; then
    "$PYTHON" -m venv "$VENV_DIR"
  fi
  if ! "$VENV_PYTHON" -c 'import importlib.util,sys; ok_yaml=importlib.util.find_spec("yaml") is not None; ok_toml=sys.version_info >= (3,11) or importlib.util.find_spec("tomli") is not None; raise SystemExit(0 if ok_yaml and ok_toml else 1)' >/dev/null 2>&1; then
    "$VENV_PYTHON" -m pip install --disable-pip-version-check 'PyYAML>=6.0.2,<7' 'tomli>=2.0.1,<3; python_version < "3.11"'
  fi
}

command -v git >/dev/null 2>&1 || { echo "Git is required." >&2; exit 2; }
PYTHON="$(find_python)" || { echo "Python 3.9+ is required." >&2; exit 2; }

mkdir -p "$CODEX_HOME"
if [ -d "$CHECKOUT/.git" ]; then
  if [ -n "$(git -C "$CHECKOUT" status --porcelain --untracked-files=all)" ]; then
    echo "Managed checkout is dirty: $CHECKOUT" >&2
    exit 2
  fi

  ensure_runtime
  if [ -f "$CHECKOUT/scripts/eas.py" ]; then
    "$VENV_PYTHON" "$CHECKOUT/scripts/install_codex.py" --personal --check || {
      echo "Existing EAS installation is not clean; refusing to update the managed checkout." >&2
      exit 2
    }
    "$VENV_PYTHON" "$CHECKOUT/scripts/eas.py" update
  else
    # Upgrade path from pre-v0.3. The managed venv supplies tomli on Python
    # 3.9/3.10 so the old installer can validate before source mutation.
    "$VENV_PYTHON" "$CHECKOUT/scripts/install_codex.py" --personal --check || {
      echo "Existing pre-v0.3 EAS installation is not clean; refusing source update." >&2
      exit 2
    }
    git -C "$CHECKOUT" fetch origin "$REF"
    git -C "$CHECKOUT" checkout "$REF"
    git -C "$CHECKOUT" merge --ff-only "origin/$REF"
  fi
elif [ -e "$CHECKOUT" ]; then
  echo "Target exists but is not a Git checkout: $CHECKOUT" >&2
  exit 2
else
  git clone --branch "$REF" --single-branch "$REPO_URL" "$CHECKOUT"
fi

ensure_runtime
"$VENV_PYTHON" -m pip install --disable-pip-version-check --upgrade "$CHECKOUT"
"$VENV_PYTHON" "$CHECKOUT/scripts/install_codex.py" --personal --dry-run
"$VENV_PYTHON" "$CHECKOUT/scripts/install_codex.py" --personal
"$VENV_PYTHON" "$CHECKOUT/scripts/install_codex.py" --personal --check

mkdir -p "$BIN_DIR"
cat >"$BIN_DIR/eas" <<EOF
#!/usr/bin/env sh
exec "$VENV_PYTHON" "$CHECKOUT/scripts/eas.py" "\$@"
EOF
chmod +x "$BIN_DIR/eas"

echo "Engineering Agent Stack installed."
echo "Managed runtime: $VENV_DIR"
echo "Launcher: $BIN_DIR/eas"
echo "PATH was not modified. Add $BIN_DIR to PATH yourself if needed."
echo "Run: $BIN_DIR/eas doctor"
