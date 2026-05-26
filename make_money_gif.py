from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import random
import math
import numpy as np

random.seed(42)
np.random.seed(42)

SIZE = 400
TOTAL_FRAMES = 55

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def get_font(size):
    try:
        return ImageFont.truetype(FONT_BOLD, size)
    except:
        return ImageFont.load_default()


def add_grain(arr, intensity=18):
    noise = np.random.randint(-intensity, intensity + 1, arr.shape, dtype=np.int16)
    return np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)


def apply_glitch(arr):
    result = arr.copy()
    for _ in range(random.randint(3, 7)):
        y = random.randint(0, SIZE - 20)
        h = random.randint(2, 18)
        shift = random.randint(-70, 70)
        strip = result[y:y + h, :].copy()
        if shift > 0:
            result[y:y + h, shift:] = strip[:, :SIZE - shift]
            result[y:y + h, :shift] = strip[:, SIZE - shift:]
        elif shift < 0:
            s = abs(shift)
            result[y:y + h, :SIZE - s] = strip[:, s:]
            result[y:y + h, SIZE - s:] = strip[:, :s]
    # Random bright bar
    if random.random() < 0.5:
        y = random.randint(0, SIZE - 5)
        h = random.randint(1, 5)
        val = random.choice([0, 255, 220])
        result[y:y + h, :] = val
    return result


def wavy_lines(draw, y_start, y_end, amp, freq, gap, brightness):
    for y_base in range(y_start, y_end, gap):
        pts = [(x, y_base + int(amp * math.sin(x * freq + y_base * 0.04))) for x in range(SIZE)]
        draw.line(pts, fill=brightness, width=1)


def centered_text(draw, text, font, fill, y_offset=0):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SIZE - tw) // 2 - bbox[0]
    y = (SIZE - th) // 2 - bbox[1] + y_offset
    draw.text((x, y), text, fill=fill, font=font)


# ── Frame generators ──────────────────────────────────────────────────────────

def frame_full_bill(denom, sym):
    img = Image.new('L', (SIZE, SIZE), 8)
    draw = ImageDraw.Draw(img)
    draw.rectangle([6, 6, SIZE - 6, SIZE - 6], outline=210, width=3)
    draw.rectangle([13, 13, SIZE - 13, SIZE - 13], outline=110, width=1)
    wavy_lines(draw, 22, 110, amp=5, freq=0.09, gap=6, brightness=38)
    wavy_lines(draw, SIZE - 110, SIZE - 22, amp=5, freq=0.09, gap=6, brightness=38)
    # Oval watermark area
    draw.ellipse([90, 110, 310, 290], outline=160, width=2)
    font_big = get_font(105)
    font_corner = get_font(42)
    font_serial = get_font(15)
    text = f"{sym}{denom}"
    centered_text(draw, text, font_big, fill=225, y_offset=-5)
    # Corners
    for cx, cy in [(18, 16), (SIZE - 65, 16), (18, SIZE - 58), (SIZE - 65, SIZE - 58)]:
        draw.text((cx, cy), str(denom), fill=175, font=font_corner)
    serial = f"{''.join([str(random.randint(0,9)) for _ in range(5)])}{''.join([chr(random.randint(65,90)) for _ in range(2)])}{''.join([str(random.randint(0,9)) for _ in range(4)])}"
    draw.text((22, SIZE // 2 + 75), serial, fill=110, font=font_serial)
    return img


def frame_texture():
    img = Image.new('L', (SIZE, SIZE), 5)
    draw = ImageDraw.Draw(img)
    freq = random.uniform(0.06, 0.16)
    amp = random.uniform(4, 9)
    for y_base in range(0, SIZE, 3):
        pts = [(x, y_base + int(amp * math.sin(x * freq + y_base * 0.05))) for x in range(SIZE)]
        brt = 50 + int(55 * abs(math.sin(y_base * 0.04)))
        draw.line(pts, fill=brt, width=1)
    return img


def frame_big_number(denom):
    img = Image.new('L', (SIZE, SIZE), 5)
    draw = ImageDraw.Draw(img)
    font = get_font(230)
    ox = random.randint(-40, 20)
    oy = random.randint(-40, 20)
    bbox = draw.textbbox((0, 0), str(denom), font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((SIZE - tw) // 2 + ox - bbox[0], (SIZE - th) // 2 + oy - bbox[1]), str(denom), fill=210, font=font)
    return img


def frame_seal():
    img = Image.new('L', (SIZE, SIZE), 5)
    draw = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2
    draw.ellipse([cx - 155, cy - 155, cx + 155, cy + 155], outline=220, width=4)
    draw.ellipse([cx - 132, cy - 132, cx + 132, cy + 132], outline=130, width=2)
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        x1 = cx + int(108 * math.cos(rad))
        y1 = cy + int(108 * math.sin(rad))
        x2 = cx + int(130 * math.cos(rad))
        y2 = cy + int(130 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=200, width=2)
    # 5-point star
    star_pts = []
    for i in range(5):
        a_out = math.radians(i * 72 - 90)
        a_in  = math.radians(i * 72 + 36 - 90)
        star_pts.append((cx + int(65 * math.cos(a_out)), cy + int(65 * math.sin(a_out))))
        star_pts.append((cx + int(28 * math.cos(a_in)),  cy + int(28 * math.sin(a_in))))
    draw.polygon(star_pts, outline=220, fill=40)
    font = get_font(28)
    centered_text(draw, "$$$", font, fill=220)
    return img


def frame_text_only(line1, line2=""):
    img = Image.new('L', (SIZE, SIZE), 5)
    draw = ImageDraw.Draw(img)
    wavy_lines(draw, 0, SIZE, amp=3, freq=0.07, gap=8, brightness=22)
    font1 = get_font(48)
    font2 = get_font(30)
    centered_text(draw, line1, font1, fill=230, y_offset=-30 if line2 else 0)
    if line2:
        centered_text(draw, line2, font2, fill=170, y_offset=30)
    return img


def frame_scatter_bills():
    img = Image.new('L', (SIZE, SIZE), 5)
    draw = ImageDraw.Draw(img)
    font = get_font(36)
    for _ in range(6):
        x = random.randint(0, SIZE - 100)
        y = random.randint(0, SIZE - 50)
        sym = random.choice(['$100', '$50', '€100', '$20'])
        draw.text((x, y), sym, fill=random.randint(140, 220), font=font)
        draw.rectangle([x - 5, y - 5, x + 95, y + 45], outline=random.randint(80, 160), width=1)
    return img


# ── Build animation sequence ──────────────────────────────────────────────────

text_frames = [
    ("FEDERAL", "RESERVE"),
    ("IN GOD", "WE TRUST"),
    ("$100", ""),
    ("€50", ""),
    ("MONEY", ""),
    ("CASH", "ONLY"),
]

bill_configs = [(100, '$'), (50, '$'), (100, '€'), (20, '$'), (50, '€'), (100, '$')]

frames_pil = []
durations = []

for i in range(TOTAL_FRAMES):
    r = random.random()

    if r < 0.06:                     # white flash
        base = Image.new('L', (SIZE, SIZE), 255)
        dur = random.choice([2, 2, 3])
    elif r < 0.10:                   # black flash
        base = Image.new('L', (SIZE, SIZE), 0)
        dur = random.choice([2, 2, 3])
    elif r < 0.22:                   # texture close-up
        base = frame_texture()
        dur = random.choice([3, 4, 4])
    elif r < 0.34:                   # giant number
        base = frame_big_number(random.choice([100, 50, 100, 20]))
        dur = random.choice([3, 3, 4])
    elif r < 0.42:                   # seal
        base = frame_seal()
        dur = random.choice([4, 5])
    elif r < 0.52:                   # scattered bills
        base = frame_scatter_bills()
        dur = random.choice([3, 4])
    elif r < 0.62:                   # text
        t = random.choice(text_frames)
        base = frame_text_only(*t)
        dur = random.choice([3, 4])
    else:                            # full bill
        d, s = random.choice(bill_configs)
        base = frame_full_bill(d, s)
        dur = random.choice([4, 5, 6])

    arr = np.array(base, dtype=np.uint8)

    # glitch ~30% of frames
    if random.random() < 0.30:
        arr = apply_glitch(arr)

    # grain
    arr = add_grain(arr, random.randint(8, 28))

    # flicker
    flicker = random.uniform(0.72, 1.28)
    arr = np.clip(arr.astype(np.float32) * flicker, 0, 255).astype(np.uint8)

    frame = Image.fromarray(arr, mode='L').convert('P')
    frames_pil.append(frame)
    durations.append(dur)  # centiseconds → each unit = 10 ms

output = '/home/user/H/money_profile.gif'
frames_pil[0].save(
    output,
    save_all=True,
    append_images=frames_pil[1:],
    optimize=False,
    duration=durations,  # PIL uses milliseconds
    loop=0
)
print(f"Saved to {output}  |  {len(frames_pil)} frames  |  avg {sum(durations)/len(durations):.1f} ms/frame")
