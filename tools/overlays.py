from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

F = '/root/.fonts/Montserrat-'
STOPS = [(0, '#18d4b2'), (.29, '#116e66'), (.50, '#148c82'), (.68, '#15a69a'), (.85, '#1bcfc0'), (1, '#21e8d7')]

def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def gradient(w, h, angle_turn=0.145):
    a = angle_turn * 2 * np.pi
    dx, dy = np.sin(a), -np.cos(a)
    ys, xs = np.mgrid[0:h, 0:w]
    p = (xs - w / 2) * dx + (ys - h / 2) * dy
    half = abs(w / 2 * dx) + abs(h / 2 * dy)
    t = (p + half) / (2 * half)
    pos = [s[0] for s in STOPS]; cols = np.array([hexrgb(s[1]) for s in STOPS], float)
    img = np.stack([np.interp(t, pos, cols[:, c]) for c in range(3)], -1)
    return Image.fromarray(img.astype(np.uint8), 'RGB')

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def title_png(text, path, W=1080):
    font = ImageFont.truetype(F + 'ExtraBold.ttf', 50)
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    lines = wrap(d, text, font, 860)
    lh = 62; pw = int(max(d.textlength(l, font=font) for l in lines)) + 80; ph = lh * len(lines) + 44
    canvas = Image.new('RGBA', (W, ph + 40), (0, 0, 0, 0))
    shadow = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    x0 = (W - pw) // 2
    ImageDraw.Draw(shadow).rounded_rectangle([x0, 14, x0 + pw, 14 + ph], 30, fill=(0, 40, 35, 110))
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(10)))
    g = gradient(pw, ph).convert('RGBA')
    mask = Image.new('L', (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], 30, fill=255)
    canvas.paste(g, (x0, 8), mask)
    dr = ImageDraw.Draw(canvas)
    for i, l in enumerate(lines):
        tw = dr.textlength(l, font=font)
        dr.text(((W - tw) / 2, 8 + 20 + i * lh), l, font=font, fill='white')
    canvas.save(path)

def name_png(path):
    f1 = ImageFont.truetype(F + 'ExtraBold.ttf', 50); f2 = ImageFont.truetype(F + 'SemiBold.ttf', 30)
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    t1, t2 = 'Катя Стриж', 'технолог по кератину · 13 лет'
    pw = int(max(d.textlength(t1, font=f1), d.textlength(t2, font=f2))) + 84; ph = 132
    img = Image.new('RGBA', (pw + 30, ph + 30), (0, 0, 0, 0))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([10, 14, 10 + pw, 14 + ph], 26, fill=(0, 40, 35, 90))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(9)))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle([8, 8, 8 + pw, 8 + ph], 26, fill=(255, 255, 255, 240))
    bar = gradient(12, ph - 36).convert('RGBA'); img.paste(bar, (30, 26))
    dr.text((60, 22), t1, font=f1, fill='#0A2F2A')
    dr.text((60, 86), t2, font=f2, fill='#116E66')
    img.save(path)

def endcard_png(path, W=1080, H=1920):
    base = Image.new('RGBA', (W, H), (8, 40, 36, 205))
    dr = ImageDraw.Draw(base)
    f1 = ImageFont.truetype(F + 'Black.ttf', 118); f2 = ImageFont.truetype(F + 'SemiBold.ttf', 40)
    t1 = 'Keratin.Expert'
    tw = dr.textlength(t1, font=f1)
    # gradient text
    mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).text(((W - tw) / 2, 780), t1, font=f1, fill=255)
    g = gradient(W, H).convert('RGBA')
    light = Image.blend(g.convert('RGB'), Image.new('RGB', (W, H), 'white'), 0.35).convert('RGBA')
    base.paste(light, (0, 0), mask)
    bw = int(tw * 0.55); bar = gradient(bw, 10).convert('RGBA')
    bm = Image.new('L', (bw, 10), 0); ImageDraw.Draw(bm).rounded_rectangle([0, 0, bw - 1, 9], 5, fill=255)
    base.paste(bar, ((W - bw) // 2, 945), bm)
    for i, t in enumerate(['Обучение кератину · Катя Стриж', 'Составы Jkeratin']):
        w2 = dr.textlength(t, font=f2); dr.text(((W - w2) / 2, 990 + i * 60), t, font=f2, fill=(230, 250, 246, 255))
    base.save(path)

if __name__ == '__main__':
    import sys
    title_png('Кератин: без этого разговора он не получится', '/home/claude/asr/frames/t_test.png')
    name_png('/home/claude/asr/frames/name.png'); endcard_png('/home/claude/asr/frames/end.png')

def name_brand_png(path):
    f1 = ImageFont.truetype(F + 'ExtraBold.ttf', 58); f2 = ImageFont.truetype(F + 'SemiBold.ttf', 30)
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    t1, t2 = 'Катя Стриж', 'технолог по кератину · 13 лет'
    pw = int(max(d.textlength(t1, font=f1), d.textlength(t2, font=f2))) + 80; ph = 150
    img = Image.new('RGBA', (pw + 40, ph + 40), (0, 0, 0, 0))
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([14, 14, 14 + pw, 14 + ph], 30, fill=(24, 212, 178, 150))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(12)))
    g = gradient(pw, ph).convert('RGBA'); m = Image.new('L', (pw, ph), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], 30, fill=255)
    img.paste(g, (14, 14), m)
    dr = ImageDraw.Draw(img)
    dr.text((54, 32), t1, font=f1, fill='white'); dr.text((56, 104), t2, font=f2, fill=(225, 255, 250, 255))
    img.save(path)

def card_png(num, text, path):
    f1 = ImageFont.truetype(F + 'Black.ttf', 44); f2 = ImageFont.truetype(F + 'ExtraBold.ttf', 36)
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    lines = wrap(d, text, f2, 330)
    ph = max(104, 30 + 44 * len(lines) + 26); pw = 96 + int(max(d.textlength(l, font=f2) for l in lines)) + 40
    img = Image.new('RGBA', (pw + 30, ph + 30), (0, 0, 0, 0))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([10, 14, 10 + pw, 14 + ph], 24, fill=(0, 40, 35, 110))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(9)))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle([8, 8, 8 + pw, 8 + ph], 24, fill=(255, 255, 255, 242))
    c = gradient(64, 64).convert('RGBA'); cm = Image.new('L', (64, 64), 0); ImageDraw.Draw(cm).ellipse([0, 0, 63, 63], fill=255)
    img.paste(c, (26, 8 + (ph - 64) // 2), cm)
    tw = dr.textlength(num, font=f1); dr.text((26 + 32 - tw / 2, 8 + (ph - 64) // 2 + 6), num, font=f1, fill='white')
    y0 = 8 + (ph - 44 * len(lines)) // 2 - 4
    for i, l in enumerate(lines): dr.text((108, y0 + i * 44), l, font=f2, fill='#0A2F2A')
    img.save(path)

def neon_end_png(path, W=1080, H=1920):
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    f1 = ImageFont.truetype(F + 'Black.ttf', 124); f2 = ImageFont.truetype(F + 'SemiBold.ttf', 50)
    t1 = 'Keratin.Expert'; d = ImageDraw.Draw(base); tw = d.textlength(t1, font=f1); x, y = (W - tw) / 2, 820
    for r, col, a in [(40, (24, 212, 178), 160), (18, (33, 232, 215), 200), (6, (33, 232, 215), 255)]:
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(L).text((x, y), t1, font=f1, fill=col + (a,))
        base = Image.alpha_composite(base, L.filter(ImageFilter.GaussianBlur(r)))
    ImageDraw.Draw(base).text((x, y), t1, font=f1, fill=(200, 255, 247, 255))
    t2 = 'Нижний Новгород'; w2 = d.textlength(t2, font=f2)
    ImageDraw.Draw(base).text(((W - w2) / 2, 1000), t2, font=f2, fill='white')
    base.save(path)

def hook_png(text, path, W=1080):
    font = ImageFont.truetype(F + 'Black.ttf', 74)
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    lines = wrap(d, text, font, 880); lh = 90
    pw = int(max(d.textlength(l, font=font) for l in lines)) + 90; ph = lh * len(lines) + 60
    img = Image.new('RGBA', (W, ph + 60), (0, 0, 0, 0)); x0 = (W - pw) // 2
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([x0, 20, x0 + pw, 20 + ph], 36, fill=(24, 212, 178, 170))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(img).rounded_rectangle([x0, 20, x0 + pw, 20 + ph], 36, fill=(6, 38, 34, 235))
    dr = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        tw = dr.textlength(l, font=font); dr.text(((W - tw) / 2, 20 + 28 + i * lh), l, font=font, fill=(255, 255, 255, 255) if i else (33, 232, 215, 255))
    img.save(path)
