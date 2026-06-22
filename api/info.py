import os
import sys
import json
import re
import subprocess
import urllib.request
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

def scrape_pinterest_image_fallback(url):
    """Scraper darurat mengekstrak direct link image HD langsung dari HTML meta Pinterest bray"""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        
        # Cari tag meta og:image bawaan Pinterest bray
        match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
            
        # Fallback regex kedua jika pola meta berbeda bray
        match2 = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html)
        if match2:
            return match2.group(1)
            
        # Taktik tebak resolusi gambar dari ID Pin jika regex gagal bray
        pin_id_match = re.search(r'pin/(\d+)', url)
        if pin_id_match:
            pin_id = pin_id_match.group(1)
            return f"https://i.pinimg.com/originals/{pin_id[:2]}/{pin_id[2:4]}/{pin_id[4:6]}/{pin_id}.jpg"
    except:
        pass
    return None

@app.route('/api/info', methods=['GET'])
def info_handler():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    # ── INTERSEPTOR PRESET PINTEREST ANTI WEB-REDIRECT ──
    if "pinterest.com" in url.lower() or "pin.it" in url.lower():
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
            
        direct_img_url = None
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            if result.returncode == 0 and result.stdout.strip():
                meta = json.loads(result.stdout.split('\n')[0])
                direct_url = meta.get("url") or meta.get("direct_url") or meta.get("thumbnail")
                
                # Jika link masih mengarah ke domain pinterest biasa, paksa bongkar html-nya bray bray bray
                if not direct_url or "pinterest.com" in direct_url or "pin.it" in direct_url:
                    direct_url = scrape_pinterest_image_fallback(url) or direct_url

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
            
        # Hard Fallback jika yt-dlp diblokir total, kita gunakan sirkuit open-graph parser bray
        direct_img_url = scrape_pinterest_image_fallback(url) or url
        return jsonify({
            "title": "Pinterest Static Artwork",
            "platform": "pinterest",
            "webpage_url": url,
            "url": direct_img_url,
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
