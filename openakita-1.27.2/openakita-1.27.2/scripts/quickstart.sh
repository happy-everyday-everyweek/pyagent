#!/usr/bin/env bash
#
# OpenAkita One-Click Install Script (PyPI)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/openakita/openakita/main/scripts/quickstart.sh | bash
#
# Recommended (download then run with parameters):
#   curl -fsSL -o quickstart.sh https://raw.githubusercontent.com/openakita/openakita/main/scripts/quickstart.sh
#   bash quickstart.sh --extras all --index-url https://pypi.tuna.tsinghua.edu.cn/simple
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

OPENAKITA_ROOT_DEFAULT="${OPENAKITA_ROOT:-$HOME/.openakita}"
OPENAKITA_APP_DIR_DEFAULT="${OPENAKITA_APP_DIR:-$OPENAKITA_ROOT_DEFAULT/app}"
OPENAKITA_VENV_DIR_DEFAULT="${OPENAKITA_VENV_DIR:-$OPENAKITA_ROOT_DEFAULT/venv}"

EXTRAS="${OPENAKITA_EXTRAS:-}"
INDEX_URL="${OPENAKITA_INDEX_URL:-}"
TORCH_MODE="${OPENAKITA_TORCH_MODE:-cpu}" # cpu|skip
INSTALL_PLAYWRIGHT="${OPENAKITA_INSTALL_PLAYWRIGHT:-1}" # 1|0
RUN_INIT="${OPENAKITA_RUN_INIT:-1}" # 1|0
INSTALL_WRAPPER="${OPENAKITA_INSTALL_WRAPPER:-1}" # 1|0
YES="${OPENAKITA_YES:-0}" # 1|0
FORCE_WRAPPER="${OPENAKITA_FORCE_WRAPPER:-0}" # 1|0

usage() {
  cat <<'EOF'
OpenAkita one-click install (PyPI).

Options:
  --dir <path>            App working directory (default: ~/.openakita/app)
  --venv <path>           Virtualenv directory (default: ~/.openakita/venv)
  --extras <list>         Extras to install, e.g. "all" or "browser,windows"
  --index-url <url>       pip index-url (mirror)
  --torch <cpu|skip>      Pre-install torch (CPU-only) or skip (default: cpu)
  --no-playwright         Skip installing Playwright browsers
  --no-init               Skip running `openakita init`
  --no-wrapper            Skip creating ~/.local/bin/openakita wrapper
  --force-wrapper         Overwrite existing wrapper if present
  -y, --yes               Non-interactive defaults
  -h, --help              Show this help

Environment variables (optional):
  OPENAKITA_ROOT, OPENAKITA_APP_DIR, OPENAKITA_VENV_DIR, OPENAKITA_EXTRAS,
  OPENAKITA_INDEX_URL, OPENAKITA_TORCH_MODE, OPENAKITA_INSTALL_PLAYWRIGHT,
  OPENAKITA_RUN_INIT, OPENAKITA_INSTALL_WRAPPER, OPENAKITA_YES, OPENAKITA_FORCE_WRAPPER
EOF
}

APP_DIR="$OPENAKITA_APP_DIR_DEFAULT"
VENV_DIR="$OPENAKITA_VENV_DIR_DEFAULT"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) APP_DIR="${2:-}"; shift 2 ;;
    --venv) VENV_DIR="${2:-}"; shift 2 ;;
    --extras) EXTRAS="${2:-}"; shift 2 ;;
    --index-url) INDEX_URL="${2:-}"; shift 2 ;;
    --torch) TORCH_MODE="${2:-}"; shift 2 ;;
    --no-playwright) INSTALL_PLAYWRIGHT="0"; shift ;;
    --no-init) RUN_INIT="0"; shift ;;
    --no-wrapper) INSTALL_WRAPPER="0"; shift ;;
    --force-wrapper) FORCE_WRAPPER="1"; shift ;;
    -y|--yes) YES="1"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; usage; exit 2 ;;
  esac
done

echo -e "${CYAN}=== OpenAkita One-Click Install ===${NC}"
echo -e "${CYAN}App dir:${NC} $APP_DIR"
echo -e "${CYAN}Venv dir:${NC} $VENV_DIR"
if [[ -n "$EXTRAS" ]]; then
  echo -e "${CYAN}Extras:${NC} $EXTRAS"
fi
if [[ -n "$INDEX_URL" ]]; then
  echo -e "${CYAN}pip index-url:${NC} $INDEX_URL"
fi
echo ""

find_python() {
  if command -v python3 >/dev/null 2>&1; then echo python3; return 0; fi
  if command -v python >/dev/null 2>&1; then echo python; return 0; fi
  return 1
}

PYTHON_CMD="$(find_python || true)"
if [[ -z "$PYTHON_CMD" ]]; then
  echo -e "${RED}Error: Python is not installed.${NC}"
  echo "Please install Python 3.11+ from https://www.python.org"
  exit 1
fi

PY_MAJOR="$("$PYTHON_CMD" -c "import sys; print(sys.version_info.major)")"
PY_MINOR="$("$PYTHON_CMD" -c "import sys; print(sys.version_info.minor)")"
PY_VER="$("$PYTHON_CMD" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")"
if [[ "$PY_MAJOR" -ne 3 || "$PY_MINOR" -lt 11 ]]; then
  echo -e "${RED}Error: Python 3.11+ required. Found: $PY_VER${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Python $PY_VER ($PYTHON_CMD)${NC}"

mkdir -p "$APP_DIR"
mkdir -p "$(dirname "$VENV_DIR")"

echo -e "${YELLOW}Creating virtual environment...${NC}"
if [[ -d "$VENV_DIR" && ! -f "$VENV_DIR/bin/activate" ]]; then
  echo -e "${YELLOW}Found incomplete venv, recreating...${NC}"
  rm -rf "$VENV_DIR"
fi
if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_CMD" -m venv "$VENV_DIR"
fi
echo -e "${GREEN}✓ venv ready${NC}"

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

PIP_INSTALL_ARGS=()
if [[ -n "$INDEX_URL" ]]; then
  PIP_INSTALL_ARGS+=( -i "$INDEX_URL" )
fi

echo -e "${YELLOW}Upgrading pip...${NC}"
python -m pip install -U pip setuptools wheel "${PIP_INSTALL_ARGS[@]}" >/dev/null
echo -e "${GREEN}✓ pip ready${NC}"

if [[ "$TORCH_MODE" == "cpu" ]]; then
  echo -e "${YELLOW}Installing PyTorch (CPU-only)...${NC}"
  python -m pip install -U torch --index-url https://download.pytorch.org/whl/cpu >/dev/null
  echo -e "${GREEN}✓ torch (CPU) installed${NC}"
elif [[ "$TORCH_MODE" == "skip" ]]; then
  echo -e "${YELLOW}Skipping torch pre-install${NC}"
else
  echo -e "${RED}Invalid --torch value: $TORCH_MODE (expected cpu|skip)${NC}"
  exit 2
fi

PKG="openakita"
if [[ -n "$EXTRAS" ]]; then
  PKG="openakita[$EXTRAS]"
fi

echo -e "${YELLOW}Installing $PKG ...${NC}"
python -m pip install -U "$PKG" "${PIP_INSTALL_ARGS[@]}"
echo -e "${GREEN}✓ OpenAkita installed${NC}"

if [[ "$INSTALL_PLAYWRIGHT" == "1" ]]; then
  echo -e "${YELLOW}Installing Playwright browsers (optional)...${NC}"
  python -m playwright install chromium >/dev/null 2>&1 || true
  # Linux deps (best-effort)
  if command -v sudo >/dev/null 2>&1; then
    sudo -n true >/dev/null 2>&1 && sudo python -m playwright install-deps chromium >/dev/null 2>&1 || true
  fi
  echo -e "${GREEN}✓ Playwright step finished${NC}"
fi

if [[ "$RUN_INIT" == "1" ]]; then
  echo -e "${YELLOW}Running setup wizard (openakita init)...${NC}"
  pushd "$APP_DIR" >/dev/null
  if [[ -t 0 ]]; then
    openakita init
  else
    # When running via pipe (curl | bash), stdin is not a tty.
    if [[ -e /dev/tty ]]; then
      exec < /dev/tty
      openakita init
    else
      echo -e "${YELLOW}No TTY available; skipping init. Run later:${NC}"
      echo "  cd \"$APP_DIR\" && source \"$VENV_DIR/bin/activate\" && openakita init"
    fi
  fi
  popd >/dev/null
fi

if [[ "$INSTALL_WRAPPER" == "1" ]]; then
  WRAPPER_DIR="$HOME/.local/bin"
  WRAPPER_PATH="$WRAPPER_DIR/openakita"
  mkdir -p "$WRAPPER_DIR"

  if [[ -f "$WRAPPER_PATH" && "$FORCE_WRAPPER" != "1" ]]; then
    echo -e "${YELLOW}Wrapper already exists, not overwriting: $WRAPPER_PATH${NC}"
    echo -e "${YELLOW}Use --force-wrapper to overwrite.${NC}"
  else
    cat > "$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$APP_DIR"
VENV_DIR="$VENV_DIR"
# shellcheck disable=SC1090
source "\$VENV_DIR/bin/activate"
cd "\$APP_DIR"
exec openakita "\$@"
EOF
    chmod +x "$WRAPPER_PATH"
    echo -e "${GREEN}✓ Wrapper installed: $WRAPPER_PATH${NC}"
  fi

  if [[ ":$PATH:" != *":$WRAPPER_DIR:"* ]]; then
    echo -e "${YELLOW}Note: $WRAPPER_DIR is not in PATH.${NC}"
    echo "Add this to your shell profile:"
    echo "  export PATH=\"$WRAPPER_DIR:\$PATH\""
  fi
fi

echo ""
echo -e "${GREEN}=== Done ===${NC}"
echo "Start:"
echo "  openakita"
echo "  openakita --help"
echo "App dir:"
echo "  $APP_DIR"
