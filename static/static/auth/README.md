# Optional login hero media

In Docker, these assets are **not** committed to git. The `webui-seed` service
downloads them from a GitHub Release (`SEED_AUTH_MEDIA_ZIP_URL`) into the shared
data volume (`SEED_AUTH_MEDIA_PATH`, default `/data/auth`). Open WebUI mounts that
directory at `/static/auth/` (so a seed that finishes after startup is visible
after a page reload, without restarting the backend).

For local non-Docker runs, you may place files here (gitignored):

- `fondo.webp` — still image / video poster (recommended ≤ 1920×1080, < 400 KB)
- `fondo.webm` — short muted loop (optional; 8–15 s, ≤ 3 MB)
- `fondo.mp4` — H.264 fallback for Safari

If these files are missing, the login page uses the SVG illustration.

Release used by the seed (example):

- https://github.com/alexcar2206/chatbot-navegation_v2/releases/download/v0.1.0-auth/docs-auth.zip

## ffmpeg example

```bash
ffmpeg -i fuente.mp4 -an -vf "scale=1920:-2" -c:v libvpx-vp9 -crf 25 -b:v 0 -t 12 fondo.webm
ffmpeg -i fuente.mp4 -an -c:v libx264 -crf 17 -preset slow -movflags +faststart -pix_fmt yuv420p fondo.mp4
# Frame at t=10.5s as poster (needs libwebp or convert via cwebp / Pillow)
ffmpeg -i fuente.mp4 -ss 10.5 -vf "scale=1920:-2" -frames:v 1 frame.png
cwebp -q 82 frame.png -o fondo.webp
```
