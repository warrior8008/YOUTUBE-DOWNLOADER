/* ─── State ─────────────────────────────────────────────────── */
let currentURL = "";
let selectedQuality = "best";
let currentMode = "video";
let pollInterval = null;

/* ─── Helpers ───────────────────────────────────────────────── */
function $(id) { return document.getElementById(id); }

function showError(msg) {
  const el = $("urlError");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 5000);
}

function formatDuration(secs) {
  if (!secs) return "";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${h}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
  return `${m}:${String(s).padStart(2,"0")}`;
}

function formatViews(n) {
  if (!n) return "";
  if (n >= 1_000_000) return `${(n/1_000_000).toFixed(1)}M views`;
  if (n >= 1_000) return `${(n/1_000).toFixed(0)}K views`;
  return `${n} views`;
}

/* ─── Mode Toggle ───────────────────────────────────────────── */
function setMode(mode) {
  currentMode = mode;
  $("modeVideo").classList.toggle("active", mode === "video");
  $("modeAudio").classList.toggle("active", mode === "audio");
  $("qualitySection").style.display = mode === "audio" ? "none" : "block";
}

/* ─── Fetch Video Info ──────────────────────────────────────── */
async function fetchInfo() {
  const url = $("urlInput").value.trim();
  if (!url) { showError("Please paste a YouTube URL."); return; }

  currentURL = url;
  const btn = $("fetchBtn");
  $("fetchBtnText").textContent = "Loading…";
  btn.disabled = true;

  // Hide previous results
  $("videoCard").classList.add("hidden");
  $("progressSection").classList.add("hidden");
  $("doneSection").classList.add("hidden");

  try {
    const res = await fetch("/api/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (data.error) { showError(data.error); return; }

    // Populate card
    $("videoThumb").src = data.thumbnail;
    $("videoTitle").textContent = data.title;
    $("videoDuration").textContent = formatDuration(data.duration);
    $("videoChannel").textContent = "📺 " + data.channel;
    $("videoViews").textContent = formatViews(data.views);

    // Build quality grid
    const grid = $("qualityGrid");
    grid.innerHTML = "";

    // Always add "Best" option
    const best = makeQualityChip("Best", "best", true);
    grid.appendChild(best);

    data.formats.forEach(f => {
      const chip = makeQualityChip(f.label, f.label, false);
      grid.appendChild(chip);
    });

    selectedQuality = "best";
    $("videoCard").classList.remove("hidden");

  } catch (err) {
    showError("Failed to connect to server. Is Flask running?");
  } finally {
    $("fetchBtnText").textContent = "Fetch";
    btn.disabled = false;
  }
}

function makeQualityChip(label, value, active) {
  const chip = document.createElement("button");
  chip.className = "quality-chip" + (active ? " selected" : "");
  chip.textContent = label;
  chip.onclick = () => selectQuality(value, chip);
  return chip;
}

function selectQuality(value, el) {
  selectedQuality = value;
  document.querySelectorAll(".quality-chip").forEach(c => c.classList.remove("selected"));
  el.classList.add("selected");
}

/* ─── Start Download ────────────────────────────────────────── */
async function startDownload() {
  if (!currentURL) return;

  $("downloadBtn").disabled = true;
  $("videoCard").classList.add("hidden");
  $("progressSection").classList.remove("hidden");
  $("doneSection").classList.add("hidden");

  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: currentURL,
        quality: selectedQuality,
        mode: currentMode,
      }),
    });
    const data = await res.json();

    if (data.error) {
      showError(data.error);
      $("videoCard").classList.remove("hidden");
      $("progressSection").classList.add("hidden");
      $("downloadBtn").disabled = false;
      return;
    }

    pollProgress(data.task_id);

  } catch (err) {
    showError("Server error. Is Flask running?");
    $("videoCard").classList.remove("hidden");
    $("progressSection").classList.add("hidden");
    $("downloadBtn").disabled = false;
  }
}

/* ─── Poll Progress ─────────────────────────────────────────── */
function pollProgress(taskId) {
  clearInterval(pollInterval);

  pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/progress/${taskId}`);
      const d = await res.json();

      const percent = d.percent || 0;
      $("progressFill").style.width = percent + "%";
      $("progressPercent").textContent = percent + "%";

      if (d.status === "downloading") {
        $("progressLabel").textContent = "Downloading…";
        $("progressSpeed").textContent = d.speed || "";
        $("progressETA").textContent = d.eta ? `ETA: ${d.eta}` : "";
      } else if (d.status === "processing") {
        $("progressLabel").textContent = "Processing with ffmpeg…";
        $("progressSpeed").textContent = "";
      } else if (d.status === "done") {
        clearInterval(pollInterval);
        showDone(d.filename);
      } else if (d.status === "error") {
        clearInterval(pollInterval);
        showError("Download failed: " + (d.error || "unknown error"));
        $("videoCard").classList.remove("hidden");
        $("progressSection").classList.add("hidden");
        $("downloadBtn").disabled = false;
      }
    } catch (e) {
      // Server temporarily unreachable — keep polling
    }
  }, 800);
}

/* ─── Show Done ─────────────────────────────────────────────── */
function showDone(filename) {
  $("progressSection").classList.add("hidden");
  $("doneSection").classList.remove("hidden");

  const link = $("downloadLink");
  link.href = `/api/file/${encodeURIComponent(filename)}`;
  link.download = filename;
}

/* ─── Reset ─────────────────────────────────────────────────── */
function resetAll() {
  clearInterval(pollInterval);
  $("urlInput").value = "";
  $("videoCard").classList.add("hidden");
  $("progressSection").classList.add("hidden");
  $("doneSection").classList.add("hidden");
  $("downloadBtn").disabled = false;
  currentURL = "";
  selectedQuality = "best";
  setMode("video");
  $("progressFill").style.width = "0%";
  $("progressPercent").textContent = "0%";
}

/* ─── Enter key on URL input ────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  $("urlInput").addEventListener("keydown", e => {
    if (e.key === "Enter") fetchInfo();
  });
});
