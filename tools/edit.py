import subprocess, os, sys, re
sys.path.insert(0, '/home/claude/asr')
import overlays as O

V = '/home/claude/vid/'
OUT = '/home/claude/out/'
os.makedirs(OUT, exist_ok=True)
P = 0.10
TAIL = 2.6  # end card length

CLIPS = {
 '01_konsultaciya_3_voprosa': ('IMG_6180.mov', 'Кератин: без этого разговора он не получится', [
   (1.92, 10.51, 'Хороший кератин начинается не с утюжка, а с разговора. Какие вопросы я задаю клиентке, чтобы у нас получился самый крутой кератин?'),
   (18.34, 21.41, 'Первое: хочет ли она сохранить объём волос?'),
   (21.66, 28.27, 'Второе: я определяю толщину волос, чтобы понять, какой состав идеально подойдёт.'),
   (28.66, 35.12, 'Третье: я спрашиваю, было ли осветление, химическая завивка или нанопластика.'),
   (35.45, 36.60, 'Это очень важно.'),
 ], ['кератин', 'разговора', 'объём', 'толщину', 'состав', 'осветление', 'завивка', 'нанопластика', 'важно']),
 '02_obyom_shlyapnaya_zona': ('IMG_6181.mov', 'Кератин и прикорневой объём: где отступать', [
   (0.90, 4.97, 'Скажите, пожалуйста, хотите ли вы сохранить объём волос?'),
   (5.77, 11.88, 'Как мы будем с вами сохранять? Отступать пару сантиметров, иногда шесть, или, может быть, вы хотите прям много отступить?'),
   (12.49, 17.10, 'В таких случаях мы отступаем именно в шляпной зоне.'),
   (22.20, 30.96, 'Нащупываем бугорки на коже головы и именно от них начинаем отступать. А здесь отступаем, как обычно, сантиметр или полтора.'),
 ], ['объём', 'сантиметров', 'шесть', 'шляпной', 'зоне', 'бугорки', 'полтора']),
 '03_pushkovye_volosy': ('IMG_6181.mov', 'Кератин на пушковые волосы у лица', [
   (32.16, 37.48, 'Скажите, пожалуйста, у вас сильно вьются волосы у корней? Нужно ли нам будет прорабатывать у корней?'),
   (55.43, 76.68, 'Вот эти пушковые волосы у вас сильно вьются, мы будем их выпрямлять. И несмотря на то, что мы отступаем от корней, пушковые волосы по краевой линии спереди и сзади мы будем прорабатывать отдельно. Внимательно наносим на них состав и отдельно прорабатываем их утюжком. Некоторым клиентам это важно, а кому не важно, там мы это не делаем.'),
 ], ['корней', 'пушковые', 'краевой', 'линии', 'отдельно', 'утюжком', 'важно']),
 '04_osvetlenie_himiya_nanoplastika': ('IMG_6181.mov', 'Кератин после осветления: что важно знать', [
   (78.46, 84.01, 'Скажите, были ли у вас осветление, химическая завивка или нанопластика? — Нет.'),
   (84.50, 100.99, 'Нет, не было. Это очень важно, потому что если было осветление, химическая завивка или нанопластика, мы иначе подбираем температуру утюжка, а также обязательно добавляем активатор S+S и рекомендуем процедуру реконструкции. В данном случае это не требуется.'),
 ], ['осветление', 'завивка', 'нанопластика', 'температуру', 'S+S', 'реконструкции', 'важно']),
 '05_tolshchina_i_sostav': ('IMG_6181.mov', 'Какой кератин выбрать под толщину волос', [
   (121.96, 128.90, 'И мы определяем, какой толщины у нас волосы: тонкие, нормальные или толстые.'),
   (131.00, 133.70, 'От этого зависит, какой состав мы будем использовать.'),
   (136.72, 143.25, 'Хотя на любые волосы мы можем использовать любой состав, но если мы хотим получить сильный эффект,'),
   (145.22, 158.20, 'то на плотные, толстые, сильно вьющиеся волосы мы используем самый сильный состав, а на тонкие волосы мы имеем возможность взять состав слабее, который будет комфортнее в работе в плане запаха.'),
 ], ['толщины', 'тонкие', 'нормальные', 'толстые', 'состав', 'сильный', 'слабее', 'запаха']),
}

def cards(text, maxlen=22):
    out, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > maxlen: out.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: out.append(cur)
    return out

def ts(t): return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat ExtraBold,70,&H00FFFFFF,&H00FFFFFF,&H00666E11,&H80000000,0,0,0,0,100,100,0,0,1,7,2,2,70,70,470,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
HL = r'{\c&H00D7E821&}'; WH = r'{\c&H00FFFFFF&}'

def highlight(card, kws):
    words = card.split()
    res = []
    for w in words:
        core = re.sub(r'[^\wё+]', '', w.lower())
        hit = any(core.startswith(k.lower().rstrip('аеиоуыяюь')[:max(4, len(k) - 2)]) or core == k.lower() for k in kws)
        res.append(HL + w + WH if hit else w)
    return ' '.join(res)

MV={'01':470,'02':400,'03':400,'04':400,'05':330}
def build(name, src, title, segs, kws, out_path, recut=True):
    tmp = OUT + 'tmp_' + name + '/'; os.makedirs(tmp, exist_ok=True)
    ranges, events, t = [], [], 0.0
    for s, e, text in segs:
        a, b = max(0, s - P), e + P
        ranges.append((a, b))
        cs = cards(text); total = sum(len(c) for c in cs); cur = t + (s - a)
        for c in cs:
            d = (e - s) * len(c) / total; events.append((cur, cur + d, c)); cur += d
        t += b - a
    D = t
    ass = OUT + name + '.ass'
    with open(ass, 'w', encoding='utf-8') as f:
        f.write(ASS_HEAD.replace(',70,70,470,1', f',70,70,{MV[name[:2]]},1'))
        for a, b, c in events: f.write(f'Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{highlight(c, kws)}\n')
    if recut:
        with open(tmp + 'list.txt', 'w') as lst:
            for i, (a, b) in enumerate(ranges):
                d = b - a; p = f'{tmp}p{i}.mov'
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-ss', f'{a:.3f}', '-i', V + src, '-t', f'{d:.3f}',
                                '-vf', 'scale=1080:1920,fps=30', '-af', f'aresample=48000,afade=t=in:d=0.04,afade=t=out:st={d-0.04:.3f}:d=0.04',
                                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'pcm_s16le', p], check=True)
                lst.write(f"file '{p}'\n")
    O.title_png(title, tmp + 'title.png'); O.name_png(tmp + 'name.png'); O.endcard_png(tmp + 'end.png')
    T = D + TAIL
    fc = (f"[0:v]tpad=stop_mode=clone:stop_duration={TAIL},subtitles={ass}[b];"
          f"[1:v]format=rgba,fade=in:st=0.15:d=0.35:alpha=1[ti];"
          f"[2:v]format=rgba,fade=in:st=0.7:d=0.35:alpha=1,fade=out:st=4.3:d=0.35:alpha=1[nm];"
          f"[3:v]format=rgba,fade=in:st={D:.2f}:d=0.45:alpha=1[en];"
          f"[b][ti]overlay=x=0:y=120:enable='lt(t,{D:.2f})'[b1];"
          f"[b1][nm]overlay=x=W-w-24:y=330:enable='between(t,0.7,4.7)'[b2];"
          f"[b2][en]overlay=0:0:enable='gte(t,{D:.2f})'[vo];"
          f"[0:a]loudnorm=I=-14:TP=-1.5,apad=pad_dur={TAIL}[ao]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-f', 'concat', '-safe', '0', '-i', tmp + 'list.txt',
                    '-loop', '1', '-t', f'{T:.2f}', '-i', tmp + 'title.png', '-loop', '1', '-t', f'{T:.2f}', '-i', tmp + 'name.png',
                    '-loop', '1', '-t', f'{T:.2f}', '-i', tmp + 'end.png', '-filter_complex', fc, '-map', '[vo]', '-map', '[ao]', '-t', f'{T:.2f}',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-b:a', '160k',
                    '-movflags', '+faststart', out_path], check=True)
    return T

if __name__ == '__main__':
    only = sys.argv[1:]
    for name, (src, title, segs, kws) in CLIPS.items():
        if only and not any(o in name for o in only): continue
        recut = name.startswith('05') or not os.path.exists(OUT + 'tmp_' + name + '/list.txt')
        print(name, round(build(name, src, title, segs, kws, OUT + name + '.mp4', recut), 1), flush=True)
