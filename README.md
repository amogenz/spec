# AMO Downloader — Deploy Guide

Self-hosted yt-dlp downloader di Vercel. Support YouTube, Instagram, Facebook.

## 📁 Struktur Project

```
amo-downloader/
├── api/
│   ├── info.py        ← endpoint: GET /api/info?url=...
│   └── download.py    ← endpoint: GET /api/download?url=...&format=...&quality=...
├── public/
│   └── index.html     ← frontend cyberpunk UI
├── requirements.txt   ← yt-dlp dependency
└── vercel.json        ← Vercel config
```

## 🚀 Cara Deploy ke Vercel

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Login Vercel
```bash
vercel login
```

### 3. Upload project
```bash
# Masuk ke folder project
cd amo-downloader

# Deploy
vercel

# Jawab pertanyaan:
# - Set up and deploy? → Y
# - Which scope? → pilih akun lo
# - Link to existing project? → N
# - Project name? → amo-downloader (atau bebas)
# - In which directory is your code located? → ./
# - Override settings? → N
```

### 4. Deploy production
```bash
vercel --prod
```

Vercel bakal kasih URL kayak: `https://amo-downloader-xxxx.vercel.app`

---

## 🔗 API Endpoints

### GET /api/info
Fetch info media dari URL.

**Params:**
- `url` — URL YouTube/Instagram/Facebook

**Response:**
```json
{
  "title": "Judul Video",
  "uploader": "Channel Name",
  "duration": "5:32",
  "views": "1.2M",
  "thumbnail": "https://...",
  "type": "video",
  "platform": "youtube",
  "formats": ["video_hd", "video_sd", "mp3"]
}
```

### GET /api/download
Dapatkan direct download URL.

**Params:**
- `url` — URL sumber
- `format` — `video_hd` / `video_sd` / `mp3` / `image_jpg` / `image_png`
- `quality` — `1080p` / `720p` / `480p` / `360p` / `320kbps` / `128kbps`

**Response:**
```json
{
  "url": "https://direct-download-url...",
  "filename": "judul-video.mp4",
  "format": "video_hd",
  "quality": "1080p"
}
```

---

## ⚙️ Format yang Didukung

| Format     | Deskripsi              |
|------------|------------------------|
| video_hd   | Video MP4 720p-1080p   |
| video_sd   | Video MP4 360p-480p    |
| mp3        | Audio MP3 128-320kbps  |
| image_jpg  | Gambar JPEG (IG foto)  |
| image_png  | Gambar PNG (IG foto)   |

---

## 🛠 Troubleshooting

**Error: "yt-dlp not found"**
→ Pastikan `requirements.txt` ada dan Vercel pakai Python runtime

**Error: "Sign in required" / "rate-limit reached or login required" (Instagram)**
→ Instagram membatasi IP datacenter. Solusi: pasang cookies Instagram sendiri
tanpa masuk ke git — set environment variable `YTDLP_COOKIES` di Vercel
(isinya = seluruh isi file `cookies.txt` format Netscape) lalu redeploy.
Cara dapat file-nya: di Chrome desktop yang sudah login instagram.com,
pasang ekstensi "Get cookies.txt LOCALLY" → export → salin isinya ke env var.
Jangan pernah commit cookies ke repo publik (akun bisa dibajak).

**Timeout**
→ Vercel free tier max 10 detik. Upgrade ke Pro untuk max 60 detik, atau gunakan `maxDuration: 60` di vercel.json (butuh Pro plan).

---

## 📝 Notes

- Gunakan untuk keperluan pribadi / edukasi
- Hormati hak cipta konten creator
- yt-dlp update otomatis via `requirements.txt`

Built by **AMOGENZ** · Mojokerto 🔥
