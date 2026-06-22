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
    
    # Deteksi codec video bray
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

    # Routing spesifikasi tombol untuk situs non-YouTube bray bray bray
    if extractor != "youtube":
        if has_video:
            formats.append("video_hd")
            formats.append("video_sd")
        if has_audio:
            formats.append("mp3")
        # Jika platform luar atau tipe medianya gambar statis, open gate image packet
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

    cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies.txt')

    # Perintah standar ekstraksi bray
    base_cmd = [
        sys.executable, "-m", "yt_dlp",
        "--dump-json",
        "--no-playlist",
        "--no-warnings",
        "--quiet",
        "--extractor-args", "youtube:player-client=ios,android_embedded"
    ]

    if os.path.exists(cookies_path):
        base_cmd.extend(["--cookies", cookies_path])

    try:
        # EKSEKUSI PERTAMA: Coba ambil format normal bray
        cmd = base_cmd + [url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        
        # JIKA ERROR (Seperti kasus Pinterest Foto "No video formats found!")
        if result.returncode != 0:
            # TAKTIK BYPASS: Paksa yt-dlp abaikan error format video dan ambil data mentah seadanya bray
            fallback_cmd = base_cmd + ["--no-check-certificates", "--ignore-errors", "--skip-download", url]
            result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=25)
            
            # Jika beneran zonk kosong total
            if not result.stdout.strip():
                # Fallback manual membuat mock data dari response parsing error bray bray bray
                if "pinterest" in url.lower():
                    payload = {
                        "title": "Pinterest Static Artwork Asset",
                        "platform": "pinterest",
                        "webpage_url": url,
                        "url": url, 
                        "formats": ["image_jpg"]
                    }
                    return jsonify(payload), 200
                raise Exception(result.stderr or "Target pipeline extraction drop.")

        meta = json.loads(result.stdout.split('\n')[0])
        
        # Atur link direct download fallback bray
        direct_url = meta.get("url") or meta.get("direct_url") or ""
        if not direct_url and meta.get("thumbnail"):
            direct_url = meta.get("thumbnail") # Gunakan thumbnail resolusi tinggi sebagai asset unduhan foto bray

        payload = {
            "title": meta.get("title") or meta.get("description") or "Universal Package Log",
            "platform": meta.get("extractor_key") or "net",
            "webpage_url": meta.get("webpage_url") or url,
            "url": direct_url,
            "formats": parse_formats(meta)
        }
        return jsonify(payload), 200

    except Exception as err:
        # Proteksi super aman: Jika Pinterest crash, paksa balikkan sirkuit mode foto biar user gak dapet eror merah bray
        if "pinterest" in url.lower():
            return jsonify({
                "title": "Pinterest Premium Asset",
                "platform": "pinterest",
                "webpage_url": url,
                "url": url,
                "formats": ["image_jpg"]
            }), 200
        return jsonify({"error": f"Intercept Core Failure: {str(err)}"}), 500

handler = app
