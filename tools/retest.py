# 31.10: перетест 06, 07, 09, 10, 11 — хук крупно с первого кадра в КАЖДОЙ версии (как у 01–05)
# + отличия от уже опубликованного, чтобы Instagram не считал дублем: лёгкий наезд камеры,
#   другой цвет, зерно, звук «вжух» на хуке. Основа — версия А (на ней нет старого хука).
import sys, os, glob, subprocess, numpy as np, wave
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import overlays as O, patch_hooks as P
from hooks_v2 import H

V = '/home/claude/obuchenie-keratin-1/videos/'
TMP = '/tmp/claude-0/-home-claude/4edc9c36-bbfd-56a0-b2f5-53f02e4ef983/scratchpad/rt/'
os.makedirs(TMP, exist_ok=True); W = 1080

R = {  # n: (base A file glob, old A title, {ver: (title, hook)})
 6: ('06A_komfort_ili_effekt.mp4', 'Кератин: комфорт или сильный эффект?', {
     'A': ('Кератин: комфорт или сильный эффект?', 'Посильнее и подольше? Сначала спроси'),
     'B': ('Обучение кератину: как выбрать состав', 'Сильный кератин или комфорт?'),
     'C': ('Какой кератин выбрать клиентке', 'Один вопрос — и состав подобран')}),
 7: ('07A_vybor_sostava_s_klientkoy.mp4', 'Кератин на тонкие волосы: выбор состава', {
     'A': ('Кератин на тонкие волосы: выбор состава', 'Тонкие волосы? Выбираю состав вживую'),
     'B': ('Обучение кератину: консультация вживую', 'Клиентка выбрала состав сама'),
     'C': ('Кератин с комфортом для тонких волос', 'Комфорт, но подольше? Пластика')}),
 9: ('09A_lyuboy_sostav_tonkie_volosy.mp4', 'Кератин на тонкие волосы: какой состав взять', {
     'A': ('Кератин на тонкие волосы: какой состав взять', 'Слабый состав на тонкие? Не обязательно'),
     'B': ('Обучение кератину: Shine, Afro или Пластика', 'Тонкие волосы? Подойдёт любой состав'),
     'C': ('Кератин на тонкие волосы: выбор состава', 'Shine, Afro или Пластика на тонкие?')}),
 10: ('10A_plastika_za_chto_lyublyu_h2.mp4', H[10][0], {
     'A': (H[10][0], 'Тонкие волосы? Беру только его'),
     'B': (H[10][1][0], 'Мой №1 состав для тонких волос'),
     'C': (H[10][2][0], 'До 5 месяцев гладкости на тонких')}),
 11: ('11A_formula_procedury_tonkie_volosy_h2.mp4', H[11][0], {
     'A': (H[11][0], 'Тонкие волосы? Моя формула кератина'),
     'B': (H[11][1][0], 'Записывай: формула для тонких'),
     'C': (H[11][2][0], '3 баночки — и тонкие волосы шёлк')}),
 12: ('12A_aktivator_kakoy_vzyat_h2.mp4', H[12][0], {
     'A': (H[12][0], 'Активатор: какой брать и когда'),
     'B': (H[12][1][0], 'Кератин без активатора? Смотри'),
     'C': (H[12][2][0], 'Какой активатор нужен именно ей?')}),
 13: ('13A_aktivatory_vsegda_h2.mp4', H[13][0], {
     'A': (H[13][0], 'Без них я не начинаю кератин'),
     'B': (H[13][1][0], 'Эти 2 активатора — в каждый кератин'),
     'C': (H[13][2][0], 'Мой секрет — 2 баночки')}),
}
# отличия версий: наезд, цвет
VAR = {'A': (1.03, 'eq=saturation=1.06:contrast=1.02'),
       'B': (1.035, 'eq=saturation=1.03:brightness=0.015'),
       'C': (1.03, 'eq=saturation=1.08:gamma=0.98,colorbalance=rs=0.02:bs=-0.02')}

def title_png(new, old, z, path, extra=0):
    font = ImageFont.truetype(O.F + 'ExtraBold.ttf', 50)
    pw, ph, lines = P.title_dims(new); opw, oph, _ = P.title_dims(old)
    pw = max(pw, int(opw * z) + 30 + extra); ph = max(ph, int(oph * z) + 22 + extra // 3)
    c = Image.new('RGBA', (W, ph + 48), (0, 0, 0, 0)); x0 = (W - pw) // 2
    sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x0, 6, x0 + pw, 6 + ph], 30, fill=(0, 40, 35, 110))
    c = Image.alpha_composite(c, sh.filter(ImageFilter.GaussianBlur(10)))
    g = O.gradient(pw, ph).convert('RGBA'); m = Image.new('L', (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], 30, fill=255)
    c.paste(g, (x0, 0), m); d = ImageDraw.Draw(c); y0 = (ph - 62 * len(lines)) // 2 - 4
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=font); d.text(((W - tw) / 2, y0 + i * 62), l, font=font, fill='white')
    c.save(path)

def whoosh(path, sr=44100):  # короткий «вжух + щелчок» на появление хука
    n = int(0.45 * sr); t = np.arange(n) / sr; rng = np.random.default_rng(3)
    noise = np.convolve(rng.normal(size=n), np.ones(12) / 12, 'same')
    env = np.sin(np.pi * np.minimum(t / 0.45, 1)) ** 2
    pop = np.sin(2 * np.pi * (900 - 600 * t / 0.45) * t) * np.exp(-t * 18)
    y = (noise * env * 0.35 + pop * 0.25); y = (y / np.abs(y).max() * 0.5 * 32767).astype(np.int16)
    with wave.open(path, 'w') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())

whoosh(TMP + 'whoosh.wav')
for n in [int(x) for x in sys.argv[1:]] or sorted(R):
    base, old_t, vers = R[n]; src = V + base
    for v, (title, hook) in vers.items():
        dst = V + f'{n:02d}{v}_' + base[4:].replace('_h2.mp4', '.mp4').replace('.mp4', '_r2.mp4')
        if os.path.exists(dst): print('skip', dst); continue
        z, eq = VAR[v]
        ty = int(960 - (960 - 120) * z) - 3 - (10 if base.endswith('_h2.mp4') else 0)
        title_png(title, old_t, z, TMP + f't{n}{v}.png', 90 if base.endswith('_h2.mp4') else 0); P.hook_png(hook, None, TMP + f'h{n}{v}.png')
        T = P.dur(src); D = T - 1.5
        fc = (f"[0:v]scale=iw*{z}:ih*{z},crop=1080:1920,{eq},noise=alls=4:allf=t[b];"
              f"[b][1:v]overlay=0:{ty}:enable='lt(t,{D:.2f})',"
              f"zoompan=z='if(lt(in,75),1.06-0.06*in/75,1)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30[v1];"
              f"[v1][2:v]overlay=0:640:enable='lt(t,2.3)'[v];"
              f"[3:a]volume=0.5[w];[0:a][w]amix=inputs=2:duration=first:normalize=0[a]")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-i', src, '-i', TMP + f't{n}{v}.png',
                        '-i', TMP + f'h{n}{v}.png', '-i', TMP + 'whoosh.wav', '-filter_complex', fc,
                        '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', dst], check=True)
        print('ok', os.path.basename(dst), os.path.getsize(dst) // 1048576, 'MB', flush=True)
