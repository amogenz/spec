import os
import sys
import json
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

def parse_formats(info):
    """Parse available formats from yt-dlp info with universal fallback support"""
    formats = []
    has_video = False
    has_audio = False
    has_image = False

    extractor = info.get("extractor_key", "").lower()
    
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
        if has_image or not has_video or "photo" in info.get("title", "").lower() or extractor == "pinterest":
            formats.append("image_jpg")
            
        if not formats:
            formats.append("video_hd")
    else:
        if has_video:
            formats.append("video_hd")
            formats.append("video_sd")
        if has_audio:
            formats.append("mp3")

    return list(set(formats))

@app.route('/api/info', methods=['GET'])
def info_handler():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    # Interseptor Darurat: Kalau link pinterest, langsung bypass cek awal jika terindikasi eror bray
    if "pinterest.com" in url.lower() or "pin.it" in url.lower():
        # Kita coba jalankan dengan taktik ignore-errors bray
        cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies.txt')
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json",
            "--no-playlist",
            "--no-warnings",
            "--quiet",
            "--ignore-errors",
            url
        ]
        if os.path.exists(cookies_path):
            cmd.extend(["--cookies", cookies_path])
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            if result.returncode == 0 and result.stdout.strip():
                meta = json.loads(result.stdout.split('\n')[0])
                direct_url = meta.get("url") or meta.get("direct_url") or meta.get("thumbnail") or url
                payload = {
                    "title": meta.get("title") or "Pinterest Premium Asset",
                    "platform": "pinterest",
                    "webpage_url": url,
                    "url": direct_url,
                    "formats": parse_formats(meta) if meta.get("formats") else ["image_jpg"]
                }
                return jsonify(payload), 200
        except:
            pass
            
        # Hard Fallback khusus Pinterest Image / Tipe Pin Foto bray bray bray
        return jsonify({
            "title": f"Pinterest Asset [ID: {url.split('/')[-1] or 'Premium'}]",
            "platform": "pinterest",
            "webpage_url": url,
            "url": url,
            "formats": ["image_jpg"]
        }), 200

    # ── SIRKUIT STANDAR UNTUK YOUTUBE / SOSMED LAIN ──
    cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies.txt')
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--dump-json",
        "--no-playlist",
        "--no-warnings",
        "--quiet",
        "--extractor-args", "youtube:player-client=ios,android_embedded",
        url
    ]
    if os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        
        # Jika yt-dlp gagal memproses link platform lain bray
        if result.returncode != 0 or not result.stdout.strip():
            raise Exception(result.stderr or "Target core stream extraction drop.")

        meta = json.loads(result.stdout.split('\n')[0])
        payload = {
            "title": meta.get("title") or "Universal Package Log",
            "platform": meta.get("extractor_key") or "net",
            "webpage_url": meta.get("webpage_url") or url,
            "url": meta.get("url") or meta.get("direct_url") or meta.get("thumbnail") or "",
            "formats": parse_formats(meta)
        }
        return jsonify(payload), 200

    except Exception as err:
        return jsonify({"error": f"Intercept Core Failure: {str(err)}"}), 500

handler = app
