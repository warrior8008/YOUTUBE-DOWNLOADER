"""
YouTube Downloader - Flask Backend
Uses yt-dlp for high-quality video/audio downloads
Fixed: filename matching, special chars, Windows path issues
"""

import os
import re
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Track download progress per task_id
progress_store = {}


def sanitize_filename(name):
    """Strip ALL characters that are illegal on Windows or cause URL issues."""
    # Remove non-ASCII characters (emojis, ₹, etc.)
    name = name.encode("ascii", "ignore").decode("ascii")
    # Remove Windows-illegal chars
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Collapse multiple spaces/dots
    name = re.sub(r'\s+', " ", name).strip()
    # Limit length
    return name[:80]


def get_video_info(url):
    """Fetch video metadata without downloading."""
    import yt_dlp

    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = []
    seen = set()

    for f in info.get("formats", []):
        height  = f.get("height")
        vcodec  = f.get("vcodec", "none")
        fps     = f.get("fps", 0)

        if vcodec == "none" or height is None:
            continue

        label = f"{height}p"
        if fps and fps > 30:
            label += f" {int(fps)}fps"
        if label in seen:
            continue
        seen.add(label)

        formats.append({
            "format_id": f["format_id"],
            "label":     label,
            "height":    height,
            "fps":       fps or 30,
            "filesize":  f.get("filesize") or f.get("filesize_approx") or 0,
        })

    formats.sort(key=lambda x: (x["height"], x["fps"]), reverse=True)

    return {
        "title":     info.get("title", "Unknown"),
        "thumbnail": info.get("thumbnail", ""),
        "duration":  info.get("duration", 0),
        "channel":   info.get("uploader", "Unknown"),
        "views":     info.get("view_count", 0),
        "formats":   formats,
        "url":       url,
    }


def do_download(url, quality, task_id, mode="video"):
    """Download video or audio in a background thread."""
    import yt_dlp

    progress_store[task_id] = {"status": "starting", "percent": 0, "filename": ""}

    # Use a unique safe base name to avoid any filename collision
    safe_base = f"ytgrab_{task_id[:8]}"

    def progress_hook(d):
        if d["status"] == "downloading":
            total      = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
            downloaded = d.get("downloaded_bytes", 0)
            percent    = int((downloaded / total) * 100) if total else 0
            progress_store[task_id].update({
                "status":  "downloading",
                "percent": percent,
                "speed":   d.get("_speed_str", ""),
                "eta":     d.get("_eta_str", ""),
            })
        elif d["status"] == "finished":
            progress_store[task_id]["status"]  = "processing"
            progress_store[task_id]["percent"] = 99

    out_template = os.path.join(DOWNLOAD_DIR, safe_base + ".%(ext)s")

    if mode == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key":             "FFmpegExtractAudio",
                "preferredcodec":  "mp3",
                "preferredquality":"320",
            }],
            "progress_hooks": [progress_hook],
            "quiet":       True,
            "no_warnings": True,
        }
        expected_ext = "mp3"
    else:
        if quality == "best":
            fmt = "bestvideo+bestaudio/best"
        else:
            height = quality.replace("p", "").split(" ")[0]
            fmt = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

        ydl_opts = {
            "format":              fmt,
            "outtmpl":             out_template,
            "merge_output_format": "mp4",
            "progress_hooks":      [progress_hook],
            "quiet":       True,
            "no_warnings": True,
        }
        expected_ext = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Find the actual output file by scanning downloads dir
        final_file = None

        # 1st try: expected name
        expected_path = os.path.join(DOWNLOAD_DIR, f"{safe_base}.{expected_ext}")
        if os.path.exists(expected_path):
            final_file = f"{safe_base}.{expected_ext}"

        # 2nd try: scan for any file starting with our safe_base
        if not final_file:
            for fname in os.listdir(DOWNLOAD_DIR):
                if fname.startswith(safe_base):
                    final_file = fname
                    break

        if not final_file:
            raise FileNotFoundError(
                f"Output file not found in {DOWNLOAD_DIR}. "
                f"Files present: {os.listdir(DOWNLOAD_DIR)}"
            )

        # Rename to a nice human-readable name
        raw_title   = info.get("title", "video") if info else "video"
        clean_title = sanitize_filename(raw_title) or safe_base
        nice_name   = f"{clean_title}.{expected_ext}"
        nice_path   = os.path.join(DOWNLOAD_DIR, nice_name)

        src_path = os.path.join(DOWNLOAD_DIR, final_file)
        if src_path != nice_path:
            os.rename(src_path, nice_path)

        progress_store[task_id] = {
            "status":   "done",
            "percent":  100,
            "filename": nice_name,
        }

    except Exception as e:
        progress_store[task_id] = {
            "status":  "error",
            "percent": 0,
            "error":   str(e),
        }


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def fetch_info():
    data = request.get_json()
    url  = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        return jsonify(get_video_info(url))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def start_download():
    data    = request.get_json()
    url     = data.get("url", "").strip()
    quality = data.get("quality", "best")
    mode    = data.get("mode", "video")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    task_id = str(uuid.uuid4())
    threading.Thread(
        target=do_download,
        args=(url, quality, task_id, mode),
        daemon=True
    ).start()

    return jsonify({"task_id": task_id})


@app.route("/api/progress/<task_id>")
def get_progress(task_id):
    return jsonify(progress_store.get(task_id, {"status": "not_found", "percent": 0}))


@app.route("/api/file/<path:filename>")
def serve_file(filename):
    """Serve the downloaded file then delete it."""
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if not os.path.exists(filepath):
        # Last-resort scan — find any file whose name contains the stem
        stem = os.path.splitext(filename)[0]
        for f in os.listdir(DOWNLOAD_DIR):
            if stem in f:
                filepath = os.path.join(DOWNLOAD_DIR, f)
                filename = f
                break
        else:
            return jsonify({"error": f"File not found: {filename}"}), 404

    @after_this_request
    def remove_file(response):
        try:
            os.remove(filepath)
        except Exception:
            pass
        return response

    return send_file(filepath, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    print("🚀 YouTube Downloader running at http://localhost:5000")
    app.run(debug=True, port=5000)
