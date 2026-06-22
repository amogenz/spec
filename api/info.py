def parse_formats(info):
    """Parse available formats from yt-dlp info with universal fallback support"""
    formats = []
    has_video = False
    has_audio = False
    has_image = False

    # Cek extractor atau jenis platform mentah bray
    extractor = info.get("extractor_key", "").lower()
    
    # Ambil data entries jika bentuknya playlist/slideshow gambar (seperti beberapa link tiktok/pinterest)
    entries = info.get("entries", [])
    if entries and not info.get("formats"):
        # Ambil sampel entri pertama buat deteksi tipe media bray
        sample = entries[0]
        if sample.get("ext") in ["jpg", "png", "jpeg", "webp"] or sample.get("vcodec") == "none":
            has_image = True
        else:
            has_video = True
            has_audio = True

    # Scanning format standar bawaan yt-dlp
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

    # ── SIRKUIT ROUTING UNIVERSAL LINK (Pinterest, TikTok, Capcut, dll) ──
    # Jika yt-dlp sukses tapi struktur formatnya tidak standar (situs non-YT), kita injeksi otomatis bray
    if extractor != "youtube":
        if has_video:
            formats.append("video_hd")
            formats.append("video_sd")
        if has_audio:
            formats.append("mp3")
        if has_image or ext in ["jpg", "png", "jpeg", "webp"] or "photo" in info.get("title", "").lower():
            formats.append("image_jpg")
        
        # Jika benar-benar kosong tapi download URL utama ada, paksa open-gate video bray
        if not formats and (info.get("url") or info.get("direct_url")):
            formats.append("video_hd")
    else:
        # Skema filter asli untuk YouTube biar fungsi lama lo GAK RUSAK bray bray bray
        if has_video:
            formats.append("video_hd")
            formats.append("video_sd")
        if has_audio:
            formats.append("mp3")

    # Bersihkan duplikasi dan kembalikan array format yang valid
    return list(set(formats))
