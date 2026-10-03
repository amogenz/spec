import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Vercel Hobby membunuh function setelah 10 detik, jadi timeout
# harus di bawah itu agar gagal dengan JSON rapi (408), bukan 504.
SUBPROCESS_TIMEOUT = 9

# Client "android" masih mengembalikan format progressive (video+audio
# satu file, mis. itag 18). Client "ios"/"web"/"default" kini hanya
# memberi DASH terpisah -> selector single-file selalu gagal dengan
# "Requested format is not available".
YT_ANDROID_ARGS = ["--extractor-args", "youtube:player-client=android"]

# Selector PROGRESSIVE-ONLY (vcodec & acodec terisi): browser tidak bisa
# menggabungkan stream DASH video-only + audio-only, jadi format merged
# (bestvideo+bestaudio) TIDAK dipakai — dulu menyebabkan video bisu.
YT_VIDEO_SELECTORS = {
    "video_hd": "best[acodec!=none][vcodec!=none][height<=1080]/best[acodec!=none][vcodec!=none]",
    "video_sd": "best[acodec!=none][vcodec!=none][height<=480]/best[acodec!=none][vcodec!=none]",
}
YT_QUALITY_VIDEO = {
    "1080p": "best[acodec!=none][vcodec!=none][height<=1080]/best[acodec!=none][vcodec!=none]",
    "720p":  "best[acodec!=none][vcodec!=none][height<=720]/best[acodec!=none][vcodec!=none]",
    "480p":  "best[acodec!=none][vcodec!=none][height<=480]/best[acodec!=none][vcodec!=none]",
    "360p":  "best[acodec!=none][vcodec!=none][height<=360]/best[acodec!=none][vcodec!=none]",
}

# Non-YouTube (IG/FB/direct): umumnya sudah progressive single-file.
GENERIC_VIDEO_SELECTORS = {
    "video_hd": "best[height<=1080][ext=mp4]/best[ext=mp4]/best",
    "video_sd": "best[height<=480][ext=mp4]/best[height<=480]/best",
}
GENERIC_QUALITY_VIDEO = {
    "1080p": "best[height<=1080][ext=mp4]/best[height<=1080]/best",
    "720p":  "best[height<=720][ext=mp4]/best[height<=720]/best",
    "480p":  "best[height<=480][ext=mp4]/best[height<=480]/best",
    "360p":  "best[height<=360][ext=mp4]/best[height<=360]/best",
}

AUDIO_QUALITY_SELECTORS = {
    "320kbps": "bestaudio[abr>=256]/bestaudio/best",
    "128kbps": "bestaudio[abr<=160]/bestaudio/best",
}

VALID_FORMATS = ("video_hd", "video_sd", "mp3", "image_jpg", "image_png")

EXT_MAP = {
    "video_hd": "mp4",
    "video_sd": "mp4",
    "mp3": "mp3",
    "image_jpg": "jpg",
    "image_png": "png",
}


def is_youtube(url):
    u = url.lower()
    return "youtube.com" in u or "youtu.be" in u


def resolve_selector(url, fmt, quality=None):
    """Pilih format selector + apakah perlu android client. Returns (selector, use_android)."""
    yt = is_youtube(url)

    if fmt == "mp3":
        # Audio: client default (android tidak punya stream audio-only)
        if quality in AUDIO_QUALITY_SELECTORS:
            return AUDIO_QUALITY_SELECTORS[quality], False
        return "bestaudio/best", False

    if fmt in ("video_hd", "video_sd"):
        if yt:
            qmap = YT_QUALITY_VIDEO
            fmap = YT_VIDEO_SELECTORS
            if quality in qmap:
                return qmap[quality], True
            return fmap[fmt], True
        qmap = GENERIC_QUALITY_VIDEO
        fmap = GENERIC_VIDEO_SELECTORS
        if quality in qmap:
            return qmap[quality], False
        return fmap[fmt], False

    # image_jpg / image_png
    return "best", False


def extract_media(url, fmt, quality=None):
    """Satu panggilan yt-dlp --dump-json untuk direct URL + judul sekaligus.

    (Sebelumnya: 2x panggilan "-g" lalu "--dump-json" — 2x lebih lambat
    dan rawan kena limit 10 detik Vercel Hobby.)
    """
    selector, use_android = resolve_selector(url, fmt, quality)

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--dump-json",
        "--no-playlist",
        "--no-warnings",
        "--quiet",
        "-f", selector,
    ]
    if use_android:
        cmd += YT_ANDROID_ARGS
    cmd += [url]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT)

    if result.returncode != 0 or not result.stdout.strip():
        err = (result.stderr or "Could not extract media").strip().split("\n")
        raise Exception(err[-1][:200] if err else "Could not extract media")

    try:
        data = json.loads(result.stdout.split("\n")[0])
    except Exception:
        raise Exception("Could not parse media info")

    direct_url = data.get("url")
    if not direct_url:
        raise Exception("No download URL found")

    title = data.get("title", "download")
    safe = "".join(c for c in title if c.isalnum() or c in " -_")[:50].strip()
    return direct_url, (safe or "download")


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        url = params.get("url", [None])[0]
        fmt = params.get("format", ["video_hd"])[0]
        quality = params.get("quality", [None])[0]

        if not url:
            self.respond(400, {"error": "Missing url parameter"})
            return

        if fmt not in VALID_FORMATS:
            self.respond(400, {"error": f"Invalid format: {fmt}"})
            return

        try:
            direct_url, filename_base = extract_media(url, fmt, quality)
            ext = EXT_MAP.get(fmt, "mp4")
            filename = f"{filename_base}.{ext}"

            self.respond(200, {
                "url": direct_url,
                "filename": filename,
                "format": fmt,
                "quality": quality or "best"
            })

        except subprocess.TimeoutExpired:
            self.respond(408, {"error": "Timeout — media processing took too long"})
        except Exception as e:
            self.respond(500, {"error": str(e)})

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
