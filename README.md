# ▶ YTGrab — YouTube Downloader

A beautiful, locally-hosted YouTube downloader with a full-quality video download UI.  
Powered by **yt-dlp** (Python) + **Flask** backend + clean dark web frontend.

---

## 📁 Project Structure

```
yt-downloader/
├── app.py                  ← Flask backend (main server)
├── requirements.txt        ← Python dependencies
├── run.sh                  ← Quick start script (Mac/Linux)
├── templates/
│   └── index.html          ← Frontend UI
├── static/
│   ├── css/style.css       ← Styles
│   └── js/app.js           ← Frontend logic
└── downloads/              ← Temp folder (auto-created, auto-cleaned)
```

---

## ⚡ Quick Start

### Step 1 — Install Python 3
- Download from https://www.python.org/downloads/ (if not installed)

### Step 2 — Install ffmpeg (REQUIRED for HD quality)
ffmpeg merges the video and audio streams for 1080p/4K quality.

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract and add the `bin/` folder to your System PATH

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

### Step 3 — Install Python dependencies
Open a terminal/command prompt in this folder and run:

```bash
pip install -r requirements.txt
```

Or on some systems:
```bash
pip3 install -r requirements.txt
```

### Step 4 — Run the server
```bash
python app.py
```

Or on Mac/Linux:
```bash
bash run.sh
```

### Step 5 — Open your browser
Go to: **http://localhost:5000**

---

## 🎯 How to Use

1. Paste any YouTube video URL into the input bar
2. Click **Fetch** — video info and available qualities will appear
3. Choose **Video** or **MP3 Audio** mode
4. Select your preferred quality (Best, 1080p, 720p, 480p, etc.)
5. Click **⬇ Download**
6. Wait for download + ffmpeg processing
7. Click **💾 Save File** to save to your computer

---

## 🔧 Features

- ✅ Download up to **4K / 2160p** quality (if available on YouTube)
- ✅ **MP3 audio** extraction at 320kbps
- ✅ Real-time download **progress bar** with speed + ETA
- ✅ Auto-merges video + audio via **ffmpeg**
- ✅ Files are served then **auto-deleted** from server
- ✅ Responsive design — works on mobile browsers too

---

## ⚠️ Important Notes

- This tool is for **personal, non-commercial use only**
- Respect **YouTube's Terms of Service** and **copyright law**
- Do not download content you don't have rights to use
- Downloaded files are temporarily stored in `downloads/` and auto-deleted after you save them

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| "Failed to connect to server" | Make sure `python app.py` is running |
| Download stuck at 99% | ffmpeg is processing; wait a moment |
| No 1080p option shown | Video may not have 1080p available |
| MP3 download fails | Ensure ffmpeg is installed and in PATH |
| Error: "Sign in to confirm age" | Video is age-restricted; yt-dlp can't bypass |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `flask` | Web server & API routes |
| `flask-cors` | Cross-origin request support |
| `yt-dlp` | YouTube video extraction & download |
| `ffmpeg` (system) | Video/audio stream merging |

---

Made with ❤️ using yt-dlp + Flask
