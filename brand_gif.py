from PIL import Image, ImageDraw, ImageFont
import numpy as np

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
BRAND = "EcomKonstiquent"
INPUT  = "/home/user/H/money_profile_slow.gif"
OUTPUT = "/home/user/H/money_profile_branded.gif"

SIZE = 320


def find_font_size(draw, text, font_path, max_width, start=44):
    for size in range(start, 12, -1):
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font, size
    return ImageFont.truetype(font_path, 13), 13


def add_branding(frame_l):
    """Take grayscale PIL image, return branded grayscale PIL image."""
    arr = np.array(frame_l, dtype=np.float32)

    # Soft dark gradient at the bottom third
    bar_h = int(SIZE * 0.32)
    for y in range(bar_h):
        fade = (y / bar_h) ** 0.6          # starts subtle, deepens toward bottom
        darken = 1.0 - fade * 0.72
        arr[SIZE - bar_h + y, :] *= darken

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'L').convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Auto-size font to fit with margin
    font, fsize = find_font_size(draw, BRAND, FONT_BOLD, SIZE - 28)
    bbox = draw.textbbox((0, 0), BRAND, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    tx = (SIZE - tw) // 2 - bbox[0]
    ty = SIZE - th - 22 - bbox[1]

    # Thin elegant line above text
    line_y = ty - 10
    draw.line([(tx, line_y), (tx + tw, line_y)], fill=(255, 255, 255, 160), width=1)

    # Strong dark outline for contrast (8-directional)
    for ox, oy in [(-2,-2),(-2,0),(-2,2),(0,-2),(0,2),(2,-2),(2,0),(2,2)]:
        draw.text((tx + ox, ty + oy), BRAND, fill=(0, 0, 0, 200), font=font)

    # 1-px softer shadow beneath
    draw.text((tx + 1, ty + 2), BRAND, fill=(0, 0, 0, 140), font=font)

    # Bright white main text
    draw.text((tx, ty), BRAND, fill=(255, 255, 255, 255), font=font)

    return img.convert('L')


# ── Load source GIF ──────────────────────────────────────────────────────────
src = Image.open(INPUT)
frames_out = []
durations  = []

try:
    while True:
        frame_l  = src.copy().convert('L').resize((SIZE, SIZE), Image.LANCZOS)
        branded  = add_branding(frame_l)
        frames_out.append(branded.quantize(colors=128, dither=1))
        durations.append(src.info.get('duration', 80))
        src.seek(src.tell() + 1)
except EOFError:
    pass

# ── Save ─────────────────────────────────────────────────────────────────────
frames_out[0].save(
    OUTPUT,
    save_all=True,
    append_images=frames_out[1:],
    optimize=True,
    duration=durations,
    loop=0,
)

import os
print(f"Saved {OUTPUT}  |  {len(frames_out)} frames  |  {os.path.getsize(OUTPUT)/1024/1024:.2f} MB")
