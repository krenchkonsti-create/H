"""
Simple quote-book video – no image editing, pure slideshow with hard cuts.
Mimics the @archivepill style: close-up book/paper/handwriting shots, fast cuts.
"""
import os
import numpy as np
from PIL import Image
import imageio

os.environ["IMAGEIO_FFMPEG_EXE"] = (
    "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
)

IMG_DIR = "/home/user/H/quote_imgs"
OUTPUT  = "/home/user/H/quote_video.mp4"

W, H  = 1080, 1920
FPS   = 30
SECS  = 2.0          # seconds per image (fast cuts like the original)
FRAMES = int(FPS * SECS)

# ── load valid images ──────────────────────────────────────────────────────────
valid = sorted([
    f for f in os.listdir(IMG_DIR)
    if f.endswith(".jpg") and os.path.getsize(os.path.join(IMG_DIR, f)) > 20_000
])
print(f"{len(valid)} images  →  {len(valid)*SECS:.0f}s total")

writer = imageio.get_writer(
    OUTPUT, fps=FPS, codec="libx264",
    ffmpeg_params=["-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p"],
)

for idx, fname in enumerate(valid):
    img = Image.open(os.path.join(IMG_DIR, fname)).convert("RGB")

    # Only resize to fill 1080×1920 – no color changes, no filters
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    new_w, new_h = int(iw * scale), int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center-crop to exact TikTok frame
    x0 = (new_w - W) // 2
    y0 = (new_h - H) // 2
    img = img.crop((x0, y0, x0 + W, y0 + H))

    arr = np.array(img, dtype=np.uint8)
    print(f"  [{idx+1:02d}/{len(valid)}] {fname}")

    for _ in range(FRAMES):
        writer.append_data(arr)

writer.close()
mb = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"\nSaved  {OUTPUT}  ({mb:.1f} MB)")
