import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio

os.environ["IMAGEIO_FFMPEG_EXE"] = (
    "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
)

IMG_DIR = "/home/user/H/video_imgs"
OUTPUT  = "/home/user/H/archivepill_video.mp4"

W, H   = 1080, 1920
FPS    = 30
SECS   = 2.8          # seconds per clip
FRAMES = int(FPS * SECS)

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_LIGHT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

QUOTES = [
    ("IF I PLAY,",          "I PLAY TO WIN."),
    ("NOTHING IS",          "HANDED TO YOU."),
    ("WHILE THEY SLEEP,",   "YOU WORK."),
    ("GRIND FOR",           "EVERYTHING."),
    ("STAY SILENT.",        "STAY FOCUSED."),
    ("EARNED,",             "NOT GIVEN."),
    ("BE OBSESSED",         "OR BE AVERAGE."),
    ("YOUR FUTURE SELF",    "IS WATCHING."),
    ("NO DAYS OFF.",        ""),
    ("WIN IN SILENCE.",     ""),
]

# ── helpers ────────────────────────────────────────────────────────────────────

def dark_grade(img: Image.Image) -> np.ndarray:
    arr = np.array(img.resize((W, H), Image.LANCZOS).convert("RGB"), dtype=np.float32)

    # partial desaturate → cinematic B&W tinted look
    lum = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
    arr = arr * 0.30 + lum[:,:,None] * 0.70

    # darken overall
    arr *= 0.72

    # cold tint: pull reds down, push blues slightly
    arr[:,:,0] *= 0.85
    arr[:,:,2] = np.clip(arr[:,:,2] * 1.10, 0, 255)

    # soft S-curve contrast
    a = arr / 255.0
    a = np.where(a < 0.5, 2*a*a, 1 - 2*(1-a)**2)
    arr = a * 255.0

    # vignette
    cx, cy = W/2, H/2
    xs = (np.arange(W) - cx)[None, :]
    ys = (np.arange(H) - cy)[:, None]
    v  = 1.0 - 0.70 * (np.sqrt(xs**2 + ys**2) / math.sqrt(cx**2 + cy**2)) ** 1.6
    arr *= v[:, :, None]

    return np.clip(arr, 0, 255).astype(np.uint8)


def make_text_overlay(line1: str, line2: str) -> np.ndarray:
    """Returns RGBA numpy array (H x W x 4)."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    # bottom gradient
    grad_h = int(H * 0.38)
    for y in range(grad_h):
        alpha = int(210 * (y / grad_h) ** 0.75)
        draw.line([(0, H - grad_h + y), (W, H - grad_h + y)], fill=(0, 0, 0, alpha))

    # fonts
    f_main = ImageFont.truetype(FONT_BOLD, 78)
    f_sub  = ImageFont.truetype(FONT_BOLD, 64)
    f_tag  = ImageFont.truetype(FONT_LIGHT, 30)

    def draw_text_with_outline(d, txt, x, y, font, fill=(255,255,255,255)):
        for ox, oy in [(-3,-3),(-3,0),(-3,3),(0,-3),(0,3),(3,-3),(3,0),(3,3)]:
            d.text((x+ox, y+oy), txt, fill=(0,0,0,200), font=font)
        d.text((x, y), txt, fill=fill, font=font)

    # position text
    if line2:
        b1 = draw.textbbox((0,0), line1, font=f_main)
        tw1 = b1[2]-b1[0]
        ty1 = H - 360
        draw_text_with_outline(draw, line1, (W-tw1)//2, ty1, f_main)

        b2 = draw.textbbox((0,0), line2, font=f_sub)
        tw2 = b2[2]-b2[0]
        ty2 = ty1 + 95
        draw_text_with_outline(draw, line2, (W-tw2)//2, ty2, f_sub,
                                fill=(220, 220, 220, 255))
    else:
        b1 = draw.textbbox((0,0), line1, font=f_main)
        tw1 = b1[2]-b1[0]
        draw_text_with_outline(draw, line1, (W-tw1)//2, H-280, f_main)

    # thin accent line
    line_y = H - 395 if line2 else H - 300
    draw.line([(W//2-160, line_y), (W//2+160, line_y)], fill=(255,255,255,120), width=1)

    # watermark top-left
    draw.text((36, 52), "@EcomKonstiquent", fill=(180,180,180,160), font=f_tag)

    return np.array(overlay)


def ken_burns(base: np.ndarray, t: float, zoom_in: bool) -> np.ndarray:
    """t in [0,1]. Returns (H,W,3) uint8."""
    s0, s1 = (1.0, 1.10) if zoom_in else (1.10, 1.0)
    scale  = s0 + (s1 - s0) * t
    nw, nh = int(W / scale), int(H / scale)
    x0 = (W - nw) // 2
    y0 = (H - nh) // 2
    crop = Image.fromarray(base).crop((x0, y0, x0+nw, y0+nh))
    return np.array(crop.resize((W, H), Image.LANCZOS))


def composite(bg: np.ndarray, overlay_rgba: np.ndarray, alpha_mul: float = 1.0) -> np.ndarray:
    """Alpha-composite overlay onto bg. Returns (H,W,3) uint8."""
    a = overlay_rgba[:,:,3:4].astype(np.float32) / 255.0 * alpha_mul
    fg = overlay_rgba[:,:,:3].astype(np.float32)
    bg_f = bg.astype(np.float32)
    out = bg_f * (1 - a) + fg * a
    return np.clip(out, 0, 255).astype(np.uint8)


# ── main ───────────────────────────────────────────────────────────────────────

valid = sorted([
    f for f in os.listdir(IMG_DIR)
    if f.endswith(".jpg") and os.path.getsize(os.path.join(IMG_DIR, f)) > 50_000
])
print(f"Using {len(valid)} images → {len(valid)*SECS:.0f}s total")

writer = imageio.get_writer(
    OUTPUT, fps=FPS, codec="libx264",
    ffmpeg_params=["-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p"],
)

for idx, fname in enumerate(valid):
    q1, q2 = QUOTES[idx % len(QUOTES)]
    print(f"  [{idx+1}/{len(valid)}] {fname}  \"{q1} {q2}\"")

    base    = dark_grade(Image.open(os.path.join(IMG_DIR, fname)))
    overlay = make_text_overlay(q1, q2)
    zoom_in = (idx % 2 == 0)

    for f in range(FRAMES):
        t     = f / max(FRAMES - 1, 1)
        frame = ken_burns(base, t, zoom_in)

        # text fade-in over first 18 frames
        alpha_mul = min(1.0, f / 18)
        frame = composite(frame, overlay, alpha_mul)
        writer.append_data(frame)

writer.close()
mb = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"\nSaved  {OUTPUT}  ({mb:.1f} MB)")
