#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  YTGrab - YouTube Downloader Setup Script
#  Run this once to set everything up, then run app.py
# ─────────────────────────────────────────────────────────────

set -e

echo ""
echo "  ▶  YTGrab - YouTube Downloader"
echo "  ─────────────────────────────"
echo ""

# 1. Check Python
python3 --version || { echo "❌ Python 3 is required. Install from https://python.org"; exit 1; }

# 2. Check ffmpeg (needed for merging video+audio)
if ! command -v ffmpeg &> /dev/null; then
  echo "⚠️  ffmpeg not found. Install it for best quality merging:"
  echo "   Ubuntu/Debian:  sudo apt install ffmpeg"
  echo "   macOS:          brew install ffmpeg"
  echo "   Windows:        https://ffmpeg.org/download.html"
  echo ""
fi

# 3. Install Python deps
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "  🚀 Starting server at http://localhost:5000"
echo "  Press Ctrl+C to stop."
echo ""

python3 app.py
