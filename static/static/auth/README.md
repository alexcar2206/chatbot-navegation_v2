# Optional login hero media

Place optional assets here (not required):

- `fondo.webp` — still image / video poster (recommended ≤ 1920×1080, < 400 KB)
- `fondo.webm` — short muted loop (8–15 s, ≤ 3 MB)
- `fondo.mp4` — H.264 fallback for Safari

If these files are missing, the login page uses the SVG illustration.

## ffmpeg example

```bash
ffmpeg -i fuente.mp4 -an -vf "scale=1280:-2" -c:v libvpx-vp9 -b:v 1M -t 12 fondo.webm
ffmpeg -i fuente.mp4 -an -vf "scale=1280:-2" -c:v libx264 -crf 28 -t 12 fondo.mp4
ffmpeg -i fuente.mp4 -vf "scale=1280:-2" -frames:v 1 -q:v 4 fondo.webp
```
