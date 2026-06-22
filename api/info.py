import os
import sys
import json
import subprocess
from flask import Flask, request, jsonify

# ── INITIALIZE COUPLING SERVERLESS APP VERCEL REQUIREMENT ──
app = Flask(__name__)

def parse_formats(info):
    """Parse available formats from yt-dlp info with universal fallback support"""
    formats = []
    has_video = False
    has_audio = False
    has_image = False

    extractor = info.get("extractor_key", "").lower()
    entries = info.get("entries", [])
    
    if entries and not info.get("formats"):
        sample = entries[0]
        if sample.get("ext") in ["jpg", "png", "jpeg", "webp"] or sample.get("vcodec") == "none":
            has_image = True
        else:
            has_video = True
            has_audio = True

    raw_formats = info.get("formats", [])
    for f in raw_formats:
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        ext = f.get("ext", "")

        if vcodec != "none":
            has_video = True
        if acodec != "none":
            has_audio = True
        if ext in ["jpg", "png", "jpeg", "webp"]:
            has_image = True

    if extractor != "youtube":
        if has_video:
            formats.append("video_hd")
            formats.append("video_sd")
        if has_audio:
            formats.append("mp3")
        if has_image or ext in ["jpg", "png", "jpeg", "webp"] or "photo" in info.get("title", "").lower():
            formats.append("image_jpg")
        
        if not formats and (info.get("url") or info.get("direct_url")):
            formats.append("video_hd")
    else:
        if has_video:
            formats.append("video_hd")
            formats.append("video_sd")
        if has_audio:
            formats.append("mp3")

    return list(set(formats))

# ── ROUTING HANDLER FOR VERCEL HTTP REQUEST ──
@app.route('/api/info', methods=['GET'])
def info_handler():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    # Lokasi file identitas anti-bot bypass cookies bray
    cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies.txt')

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--dump-json",
        "--no-playlist",
        "--no-warnings",
        "--quiet",
        "--extractor-args", "youtube:player-client=ios,android_embedded"
    ]

    if os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25, check=True)
        meta = json.loads(result.stdout)
        
        payload = {
            "title": meta.get("title", "Universal Package Log"),
            "platform": meta.get("extractor_key", "net"),
            "webpage_url": meta.get("webpage_url", url),
            "url": meta.get("url") or meta.get("direct_url") or "",
            "formats": parse_formats(meta)
        }
        return jsonify(payload), 200

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or "Matrix parsing failure."
        return jsonify({"error": f"Scraper Engine Error: {error_msg}"}), 500
    except Exception as err:
        return jsonify({"error": f"System Intercept Error: {str(err)}"}), 500

# Fallback Vercel interface standard bray bray bray
handler = app
