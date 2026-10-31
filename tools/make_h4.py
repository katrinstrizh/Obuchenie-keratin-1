# 01.11: пересборка роликов ИЗ ИСХОДНИКОВ по правилам 22–23 (+ просьба Кати: важные мысли текстом,
# анимация, наезды камеры). Файл: videos/NNX_<имя>_h4.mp4
#  - хук крупно по центру с первого кадра во ВСЕХ версиях + звук «вжух»
#  - кадрирование ближе на 15–20% (разное в А/Б/В), плавный отъезд 0–2,5 с, наезды/пробивки
#  - субтитры по одному слову с подсветкой ключевых слов, карточки на цифрах (+ щелчок)
#  - «главные мысли» плашками с выездом, разный цвет версий, финал/«Катя Стриж» 4–7 с как раньше
# Запуск: python3 make_h4.py 06 07 ...   (берёт куски из /home/claude/out/tmp_<имя>/, субтитры из <имя>.ass)
import sys, os, re, glob, subprocess, wave, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import overlays as O, patch_hooks as P
from hooks_v2 import H
from hooks_a import HA

OUT = '/home/claude/out/'; V = '/home/claude/obuchenie-keratin-1/videos/'
TMP = '/home/claude/h4/'; os.makedirs(TMP, exist_ok=True)
W = 1080; TAIL = 1.5
src_retest = open(os.path.dirname(os.path.abspath(__file__)) + '/retest.py', encoding='utf-8').read()
_ns = {'H': H}; exec(src_retest[src_retest.index('R = {'):src_retest.index('# отличия версий')], _ns); R = _ns['R']

NAMES = {int(os.path.basename(d)[4:6]): os.path.basename(d)[4:] for d in glob.glob(OUT + 'tmp_[0-9][0-9]_*')}

# --- кусочки: (номер ролика, индекс фразы, [начало, конец] внутри фразы) ---
def default_pieces(n): return [(n, i, None) for i in range(len(segs(n)))]
PIECES = {
    9: lambda: [(9, i, None) for i in range(5)] + [(10, 0, None), (10, 1, None)],   # мысль до конца: «...будет Пластика»
    16: lambda: [(16, 2, (9.2, None)), (16, 3, None), (16, 0, None), (16, 1, None), (16, 2, (0, 9.2))],  # «10% — золотая формула» вперёд
}
# --- главные мысли: (слово-якорь, текст) ---
TH = {
 6: [('Пластика', 'Комфорт — это Пластика'), ('Shine', 'Сильный эффект — Shine или Afro')],
 7: [('важно?', 'Сначала спроси, что ей важнее'), ('Пластику', 'Тонкие + комфорт = Пластика')],
 9: [('любой', 'На тонкие подойдёт любой состав'), ('запах.', 'Shine — сильнее, но сильный запах')],
 10: [('желтизну.', 'Нейтрализует желтизну на блонде'), ('изнутри.', 'Восстанавливает волос изнутри')],
 11: [('объём.', 'Отступ от корней = свой объём'), ('Aid', 'Пластика + Extra Gloss + Keratin Aid')],
 12: [('активатора,', 'Можно и без активатора'), ('расскажите', 'Расскажи клиентке про активаторы')],
 13: [('Shine,', 'Extra Gloss — во все, кроме Shine'), ('запах.', 'Keratin Aid снижает запах')],
 14: [('осветлены', 'Осветлённые волосы → S+S'), ('блестящими.', 'Реконструкция + кератин = блеск')],
 15: [('мягкости.', 'Коллаген — для мягкости'), ('экономичнее.', 'Жидкий активатор = экономия')],
 16: [('циферку.', 'Закрой одну цифру = 10%'), ('ошибётесь', '10% от массы — без ошибок')],
 17: [('сильнее.', 'Сильный состав пахнет сильнее'), ('густые,', 'Пористые и густые — пахнут сильнее')],
 18: [('зажимом', 'Пробор — открытым зажимом'), ('уха,', 'От макушки до кончика уха')],
 19: [('пополам,', 'Не дели затылок пополам'), ('опытом', 'С опытом — затылок целиком')],
 20: [('пластика.', 'Пробор строго по линии'), ('вьющихся', 'Ровный пробор важен на кудрях')],
 21: [('много', 'Много состава сразу'), ('излишки.', 'Потом — счесать излишки')],
 22: [('толстыми', 'Толстые пряди = быстрее'), ('виски', 'Виски — пополам или на 3')],
 23: [('скорости.', 'Секрет скорости — много состава'), ('пропитана.', 'Прядь пропитана целиком')],
 24: [('ребро', 'Излишки — ребром расчёски'), ('следующую', 'Излишки — на следующую прядь')],
 25: [('корням', 'Закрутка — к корням зажимом'), ('нависают,', 'Ошибка: прядь нависает')],
 26: [('недостаточное', 'Ошибка: мало состава'), ('счесали', 'Нанесли → распределили → счесали')],
}
NUMW = {'три': '3', 'третья': '3', 'четыре': '4', 'пять': '5', 'пополам': '½'}
# версии: кадрирование (zoom, cx, cy) и цвет
VER = {'A': (1.18, 0.50, 0.42, 'eq=saturation=1.07:contrast=1.03'),
       'B': (1.20, 0.47, 0.41, 'eq=saturation=1.03:brightness=0.012,colorbalance=bs=0.025:gs=0.01:rs=-0.01'),
       'C': (1.15, 0.53, 0.43, 'eq=saturation=1.09:gamma=0.98,colorbalance=rs=0.025:bs=-0.02')}

def dur(p): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).decode())
_seg = {}
def segs(n):
    if n not in _seg:
        tmp = OUT + 'tmp_' + NAMES[n] + '/'
        ps = [l.split("'")[1] for l in open(tmp + 'list.txt') if l.strip()]
        _seg[n] = [(p, dur(p)) for p in ps]
    return _seg[n]

def tsec(s): h, m, x = s.split(':'); return int(h) * 3600 + int(m) * 60 + float(x)
def cards(n):  # [(start, end, [(word, is_kw)])] во времени базы n
    res = []
    for l in open(OUT + NAMES[n] + '.ass', encoding='utf-8'):
        if not l.startswith('Dialogue'): continue
        f = l.rstrip('\n').split(',', 9); txt = f[9]; words = []; kw = False
        for tok in re.split(r'(\{[^}]*\})', txt):
            if tok.startswith('{'): kw = 'D7E821' in tok; continue
            for w in tok.split():
                if re.fullmatch(r'[—–-]+', w) and words: words[-1] = (words[-1][0] + ' ' + w, words[-1][1])
                else: words.append((w, kw))
        res.append((tsec(f[1]), tsec(f[2]), words))
    return res

def vw(w): return max(1, len(re.findall(r'[аеёиоуыэюяaeiouy]', w.lower()))) + 0.4
def words_timeline(n, pieces):
    """слова с временем в итоговом ролике + границы фраз"""
    out, bounds, t0 = [], [], 0.0
    for (m, i, rng) in pieces:
        sg = segs(m); off = sum(d for _, d in sg[:i]); d = sg[i][1]
        a, b = (rng or (0, None)); a = a or 0; b = d if (not rng or rng[1] is None) else rng[1]
        for (cs, ce, ws) in cards(m):
            if not (off - 0.05 <= cs < off + d - 0.05): continue
            tot = sum(vw(w) for w, _ in ws); t = cs
            for w, k in ws:
                wd = (ce - cs) * vw(w) / tot; loc = t - off
                if a - 0.05 <= loc < b - 0.05: out.append((t0 + loc - a, t0 + loc - a + wd, w, k))
                t += wd
        bounds.append(t0); t0 += b - a
    return out, bounds, t0

def cut(n, pieces, path):
    if os.path.exists(path): return
    ins, fc = [], []
    for k, (m, i, rng) in enumerate(pieces):
        p, d = segs(m)[i]; a, b = (rng or (0, None)); a = a or 0; b = d if (not rng or rng[1] is None) else rng[1]
        ins += ['-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', p]
        fc.append(f'[{k}:v]setpts=PTS-STARTPTS[v{k}];[{k}:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={b-a-0.03:.3f}:d=0.03[a{k}]')
    fc.append(''.join(f'[v{k}][a{k}]' for k in range(len(pieces))) + f'concat=n={len(pieces)}:v=1:a=1[v][a]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2'] + ins + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '[a]',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'pcm_s16le', path], check=True)

# --- графика ---
def plate(text, path, fs=56, maxw=820, first_cyan=False, label=None):
    font = ImageFont.truetype(O.F + 'Black.ttf', fs); lf = ImageFont.truetype(O.F + 'ExtraBold.ttf', 34)
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10))); lines = O.wrap(d, text, font, maxw); lh = int(fs * 1.22)
    pw = int(max(d.textlength(l, font=font) for l in lines)) + 80; top = 46 if label else 22
    ph = lh * len(lines) + top + 26; img = Image.new('RGBA', (W, ph + 50), (0, 0, 0, 0)); x0 = (W - pw) // 2
    gl = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle([x0, 14, x0 + pw, 14 + ph], 30, fill=(24, 212, 178, 150))
    img = Image.alpha_composite(img, gl.filter(ImageFilter.GaussianBlur(14)))
    dr = ImageDraw.Draw(img); dr.rounded_rectangle([x0, 14, x0 + pw, 14 + ph], 30, fill=(6, 38, 34, 245))
    if label: dr.text((x0 + 40, 14 + 14), label, font=lf, fill=(33, 232, 215, 255))
    for i, l in enumerate(lines):
        tw = dr.textlength(l, font=font)
        dr.text(((W - tw) / 2, 14 + top + i * lh), l, font=font, fill=(33, 232, 215, 255) if (first_cyan and i == 0) else (255, 255, 255, 255))
    img.save(path); return img.size

def num_png(num, cap, path):
    f1 = ImageFont.truetype(O.F + 'Black.ttf', 118); f2 = ImageFont.truetype(O.F + 'ExtraBold.ttf', 40)
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10))); w1 = d.textlength(num, font=f1); w2 = d.textlength(cap, font=f2) if cap else 0
    pw = int(max(w1, w2, 170)) + 70; ph = 150 + (52 if cap else 0)
    img = Image.new('RGBA', (pw + 50, ph + 50), (0, 0, 0, 0))
    gl = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle([25, 25, 25 + pw, 25 + ph], 34, fill=(24, 212, 178, 170))
    img = Image.alpha_composite(img, gl.filter(ImageFilter.GaussianBlur(14)))
    g = O.gradient(pw, ph).convert('RGBA'); m = Image.new('L', (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], 34, fill=255)
    img.paste(g, (25, 25), m); dr = ImageDraw.Draw(img)
    dr.text((25 + (pw - w1) / 2, 25 + 8), num, font=f1, fill='white')
    if cap: dr.text((25 + (pw - w2) / 2, 25 + 150), cap, font=f2, fill='white')
    img.save(path); return img.size

def sfx(path, kind, sr=44100):
    if kind == 'whoosh':
        n = int(0.45 * sr); t = np.arange(n) / sr; rng = np.random.default_rng(3)
        noise = np.convolve(rng.normal(size=n), np.ones(12) / 12, 'same'); env = np.sin(np.pi * np.minimum(t / 0.45, 1)) ** 2
        y = noise * env * 0.35 + np.sin(2 * np.pi * (900 - 600 * t / 0.45) * t) * np.exp(-t * 18) * 0.25; g = 0.5
    else:  # pop
        n = int(0.18 * sr); t = np.arange(n) / sr
        y = np.sin(2 * np.pi * (1400 - 700 * t / 0.18) * t) * np.exp(-t * 30); g = 0.35
    y = (y / np.abs(y).max() * g * 32767).astype(np.int16)
    with wave.open(path, 'w') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())

def ts(t): return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'
ASS = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: W,Montserrat Black,104,&H00FFFFFF,&H00FFFFFF,&H00222606,&H90000000,0,0,0,0,100,100,0,0,1,9,3,2,60,60,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def build(n, v):
    name = NAMES[n]; dst = V + f'{n:02d}{v}_{name[3:]}_h4.mp4'
    if os.path.exists(dst): print('skip', dst, flush=True); return dst
    if n in R: title, hook = R[n][2][v]
    else: title = H[n][0] if v == 'A' else H[n][{'B': 1, 'C': 2}[v]][0]; hook = HA[n] if v == 'A' else H[n][{'B': 1, 'C': 2}[v]][1]
    pieces = PIECES[n]() if n in PIECES else default_pieces(n)
    base = TMP + f'cut_{n:02d}.mp4'; cut(n, pieces, base)
    words, bounds, D = words_timeline(n, pieces); T = D + TAIL
    tmp = TMP + f'{n:02d}{v}/'; os.makedirs(tmp, exist_ok=True)
    # субтитры по слову (пока висит хук 0–2,3 с — тоже идут: хук по центру, слово внизу)
    with open(tmp + 'w.ass', 'w', encoding='utf-8') as f:
        f.write(ASS)
        for i, (a, b, w, k) in enumerate(words):
            nb = words[i + 1][0] if i + 1 < len(words) else b
            e = min(max(b, a + 0.18), nb if nb - a > 0.12 else a + 0.18, D)
            col = r'{\c&H00D7E821&}' if (k or re.search(r'\d', w)) else ''
            f.write(f'Dialogue: 0,{ts(a)},{ts(e)},W,,0,0,0,,{{\\fscx82\\fscy82\\t(0,90,\\fscx100\\fscy100)}}{col}{w}\n')
    # мысли и цифры
    ov = []  # (png, t0, t1, x, y, kind)
    taken = []
    starts = []
    for k, (anc, txt) in enumerate(TH.get(n, [])):
        cand = [a for a, b, w, kk in words if w.lower().startswith(anc.lower().rstrip('.,?')) and a > 2.4 and all(abs(a - t) > 2.6 for t, _ in starts)]
        if not cand: print('  нет якоря', n, anc, flush=True); continue
        t0 = cand[0]
        if 3.8 < t0 < 7.2: t0 = 7.15  # не мешать «Катя Стриж»
        starts.append((t0, txt))
    starts.sort()
    for k, (t0, txt) in enumerate(starts):
        t1 = min(t0 + 3.2, D - 0.2, starts[k + 1][0] - 0.15 if k + 1 < len(starts) else 1e9)
        if t1 - t0 < 1.5: continue
        plate(txt, tmp + f'th{k}.png', fs=64, label='ГЛАВНОЕ'); ov.append((tmp + f'th{k}.png', t0, t1, 0, 1060, 'th')); taken.append((t0, t1))
    for i, (a, b, w, k) in enumerate(words):
        core = w.strip('.,!?:;—«»').lower(); num = None
        if re.search(r'\d', core): num = w.strip('.,!?:;—«»')
        elif core in NUMW: num = NUMW[core]
        if not num or a < 2.4 or any(t - 0.3 < a < e + 0.3 for t, e in taken) or 3.8 < a < 7.2: continue
        cap = ''
        if i + 1 < len(words):
            nx = words[i + 1][2].strip('.,!?:;—«»')
            if re.fullmatch(r'[а-яё%]+', nx.lower()) and len(nx) <= 11 and nx.lower() not in ('это', 'и', 'а', 'на', 'значит', 'тогда'): cap = nx
        if num == '½': num, cap = '½', 'пополам'
        t0 = a; t1 = min(a + 1.7, D - 0.2)
        sz = num_png(num, cap, tmp + f'n{i}.png'); ov.append((tmp + f'n{i}.png', t0, t1, W - sz[0] - 30, 860, 'num')); taken.append((t0, t1))
    # камера: отъезд 0–2,5 с, потом наезды по фразам и «пробивка» на каждой мысли/цифре
    Z0, CX, CY, EQ = VER[v]
    kf = [(0, Z0 * 1.12), (0.6, Z0 * 1.09), (1.4, Z0 * 1.03), (2.5, Z0)]
    for j, bt in enumerate(bounds):
        if bt <= 2.5: continue
        nb = bounds[j + 1] if j + 1 < len(bounds) else D
        if j % 2: kf += [(bt, Z0 * 1.07), (nb - 0.04, Z0 * 1.10)]
        else: kf += [(bt, Z0), (nb - 0.04, Z0 * 1.04)]
    for png, t0, t1, x, y, kind in ov:  # плавный наезд, пока висит мысль
        kf = [(t, z) for t, z in kf if not (t0 - 0.05 < t < t1 + 0.05)]
        zb = Z0 * 1.02; kf += [(t0, zb), (t0 + 0.5, zb * 1.06), (t1, zb * 1.08), (t1 + 0.05, Z0 * 1.03)]
    kf = sorted(kf); kf.append((D, kf[-1][1])); kf.append((D + 0.001, 1.0)); kf.append((T + 1, 1.0))
    e = '1'
    for (a, za), (b, zb) in reversed(list(zip(kf, kf[1:]))):
        if b - a < 1e-3: continue
        e = f"if(between(it,{a:.3f},{b:.3f}),{za:.4f}+({zb:.4f}-{za:.4f})*(it-{a:.3f})/{b - a:.3f},{e})"
    z = e.replace('it', '(in/30)')
    O.title_png(title, tmp + 'title.png'); P.hook_png(hook, None, tmp + 'hook.png')
    if not os.path.exists(TMP + 'nameb.png'): O.name_brand_png(TMP + 'nameb.png'); O.neon_end_png(TMP + 'neon.png'); sfx(TMP + 'whoosh.wav', 'whoosh'); sfx(TMP + 'pop.wav', 'pop')
    ins = ['-i', base]
    for p in [tmp + 'title.png', tmp + 'hook.png', TMP + 'nameb.png', TMP + 'neon.png']: ins += ['-loop', '1', '-t', f'{T:.2f}', '-i', p]
    for o in ov: ins += ['-loop', '1', '-t', f'{T:.2f}', '-i', o[0]]
    ins += ['-i', TMP + 'whoosh.wav'] + sum([['-i', TMP + 'pop.wav'] for _ in ov], [])
    fc = [f"[0:v]tpad=stop_mode=add:stop_duration={TAIL}:color=black,zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{CX}*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{CY}*ih-ih/zoom/2))':d=1:s=1080x1920:fps=30,{EQ},subtitles={tmp}w.ass[b0]",
          "[1:v]format=rgba,fade=in:st=0.1:d=0.3:alpha=1[ti]",
          "[3:v]format=rgba,fade=in:st=4.0:d=0.3:alpha=1,fade=out:st=6.8:d=0.3:alpha=1[nm]",
          f"[4:v]format=rgba,fade=in:st={D:.2f}:d=0.25:alpha=1[en]",
          "[2:v]format=rgba,fade=out:st=2.05:d=0.25:alpha=1[hk]",
          f"[b0][ti]overlay=0:120:enable='lt(t,{D:.2f})'[b1]",
          "[b1][nm]overlay=W-w-20:320:enable='between(t,4.0,7.1)'[b2]"]
    last = 'b2'
    for k, (png, t0, t1, x, y, kind) in enumerate(ov):
        ii = 5 + k
        fc.append(f"[{ii}:v]format=rgba,fade=in:st={t0:.2f}:d=0.2:alpha=1,fade=out:st={t1 - 0.25:.2f}:d=0.25:alpha=1[o{k}]")
        if kind == 'th': pos = f"x='-W*max(0,1-(t-{t0:.2f})/0.28)':y={y}"
        else: pos = f"x={x}:y='{y}+90*max(0,1-(t-{t0:.2f})/0.22)'"
        fc.append(f"[{last}][o{k}]overlay={pos}:enable='between(t,{t0:.2f},{t1:.2f})'[c{k}]"); last = f'c{k}'
    fc += [f"[{last}][hk]overlay=0:640:enable='lt(t,2.3)'[b3]", f"[b3][en]overlay=0:0:enable='gte(t,{D:.2f})'[vo]"]
    na = 5 + len(ov)
    au = [f"[0:a]loudnorm=I=-14:TP=-1.5,apad=pad_dur={TAIL}[va]", f"[{na}:a]volume=0.55[s0]"]
    for k, o in enumerate(ov): d_ms = int(o[1] * 1000); au.append(f"[{na + 1 + k}:a]adelay={d_ms}|{d_ms},volume=0.8[s{k + 1}]")
    au.append('[va]' + ''.join(f'[s{k}]' for k in range(len(ov) + 1)) + f'amix=inputs={len(ov) + 2}:duration=first:normalize=0[ao]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2'] + ins + ['-filter_complex', ';'.join(fc + au), '-map', '[vo]', '-map', '[ao]',
                    '-t', f'{T:.2f}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-r', '30',
                    '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', dst], check=True)
    print('ok', os.path.basename(dst), round(T, 1), 's', os.path.getsize(dst) // 1048576, 'MB', flush=True)
    return dst

if __name__ == '__main__':
    vers = os.environ.get('VERS', 'ABC')
    for a in sys.argv[1:]:
        for v in vers: build(int(a), v)
