#!/usr/bin/env bash
# ==============================================================
#  Jarvis Headless Installer for Raspberry Pi 4B / 5
# ==============================================================
#  Usage: chmod +x setup.sh && ./setup.sh
#
#  What this script does:
#   1. Installs system packages
#   2. Creates a Python virtual environment
#   3. Installs Python dependencies
#   4. Installs Ollama and pulls Qwen 2.5:1.5b
#   5. Builds whisper.cpp and downloads the model
#   6. Downloads the Piper TTS voice
#   7. Creates a local .env template if needed
# ==============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
info() { echo -e "${YELLOW}[..]${NC} $*"; }
fail() { echo -e "${RED}[!!]${NC} $*"; exit 1; }

info "Installing system packages..."
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-dev \
  build-essential cmake git curl wget \
  python3-picamera2 \
  portaudio19-dev libasound2-dev \
  alsa-utils
ok "System packages installed"

VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
  info "Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
ok "Virtual environment ready ($VENV_DIR)"

info "Installing Python packages..."
pip install -q -r requirements.txt
ok "Python packages installed"

if ! command -v ollama &>/dev/null; then
  info "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi
ok "Ollama installed"

info "Pulling qwen2.5:1.5b (this may take a few minutes)..."
ollama pull qwen2.5:1.5b
ok "Qwen 2.5:1.5b ready"

if [ ! -f "/usr/local/bin/whisper-cpp" ]; then
  if [ ! -d "whisper.cpp" ]; then
    info "Cloning whisper.cpp..."
    git clone https://github.com/ggerganov/whisper.cpp.git
  fi

  info "Building whisper.cpp..."
  cd whisper.cpp
  cmake -B build
  cmake --build build --config Release -j"$(nproc)"
  sudo cp build/bin/whisper-cli /usr/local/bin/whisper-cpp
  ok "whisper.cpp installed to /usr/local/bin/whisper-cpp"

  info "Downloading whisper base.en model..."
  bash models/download-ggml-model.sh base.en
  if [ -f build/bin/quantize ]; then
    ./build/bin/quantize models/ggml-base.en.bin models/ggml-base.en-q5_0.bin q5_0
    ok "Whisper model quantized (q5_0)"
  fi
  cd "$SCRIPT_DIR"
else
  ok "whisper.cpp already installed"
fi

VOICE_DIR="piper/voices"
VOICE_FILE="$VOICE_DIR/en_GB-semaine-medium.onnx"
if [ ! -f "$VOICE_FILE" ]; then
  info "Downloading Piper TTS voice..."
  mkdir -p "$VOICE_DIR"
  wget -q -O "$VOICE_FILE" \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx
  wget -q -O "${VOICE_FILE}.json" \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/semaine/medium/en_GB-semaine-medium.onnx.json
  ok "Piper voice downloaded"
else
  ok "Piper voice already present"
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  info "Created .env from template. Add API keys only if you need cloud features."
fi

echo ""
echo "============================================================"
echo " Jarvis is installed"
echo "============================================================"
echo ""
echo " Next steps:"
echo "   1. (Optional) Edit .env to add API keys."
echo "   2. Start (backend + voice + remote control):"
echo "        source venv313/bin/activate"
echo "        python main.py --mode all"
echo ""
echo ' Say "Hey Jarvis" and start talking. The backend API runs on port 8080.'
echo ""
