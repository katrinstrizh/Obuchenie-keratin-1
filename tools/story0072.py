import subprocess, sys
sys.path.insert(0, '/home/claude/asr')
import overlays as O

S = '/tmp/claude-0/-home-claude/2d66be8e-dd3c-5a01-9f74-9682d005a419/scratchpad/'
SRC = S + 'src.mov'
OUT = S + 'story_0072_keratin_expert.mp4'

K = [(0.0, 1.62), (1.95, 4.30), (4.40, 5.02), (5.12, 6.50), (6.80, 9.00), (9.20, 9.85), (10.05, 10.97), (12.10, 17.50)]
SUB = [
    ['Всем привет,', 'проверка связи.'],
    ['Это видео —', 'моя первая попытка'],
    ['выложить'],
    ['через <искусственный интеллект>'],
    ['<сториз> сразу', 'во <все> мои аккаунты'],
    ['Просто'],
    ['с телефона'],
    ['<Одним движением>', 'он должен', 'и <смонтировать,>', 'и <выложить везде.>', 'Посмотрим,', 'что получится', 'и не <накосячит> ли он'],
]
END = 1.3

# new timeline
starts, t = [], 0.0
for a, b in K: starts.append(t); t += b - a
TOTAL = t

def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f'{h}:{m:02d}:{s:05.2f}'

ass = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 1080', 'PlayResY: 1920', '',
       '[V4+ Styles]',
       'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
       'Style: S,Montserrat ExtraBold,70,&H00FFFFFF,&H00FFFFFF,&H00666E11,&H64000000,0,0,0,0,100,100,0,0,1,6,2,2,60,60,400,1',
       '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
for (a, b), st, chunks in zip(K, starts, SUB):
    d = b - a; L = sum(len(c) for c in chunks); cur = st
    for c in chunks:
        dur = d * len(c) / L
        txt = c.replace('<', '{\\c&HD7E821&}').replace('>', '{\\c&HFFFFFF&}')
        ass.append(f'Dialogue: 0,{ts(cur)},{ts(cur + dur - 0.02)},S,,0,0,0,,{txt}')
        cur += dur
open(S + 'story.ass', 'w').write('\n'.join(ass) + '\n')

# graphics
O.title_png('Эксперимент Keratin.Expert: сториз через ИИ', S + 'g_title.png')
O.name_brand_png(S + 'g_name.png')
O.card_png('1', 'Монтаж делает ИИ', S + 'g_c1.png')
O.card_png('2', 'Одно видео → все аккаунты', S + 'g_c2.png')
O.card_png('3', 'Публикация одним движением', S + 'g_c3.png')
O.neon_end_png(S + 'g_end.png')

# windows on new timeline
W = [('g_name.png', 0.3, 3.7), ('g_c1.png', starts[3] - 0.1, starts[4]), ('g_c2.png', starts[4], starts[7]),
     ('g_c3.png', starts[7] + 0.1, starts[7] + 3.6)]

pieces = []
for i, (a, b) in enumerate(K):
    z = 1.0 if i < 7 else 1.07
    crop = '' if z == 1.0 else f'crop=iw/{z}:ih/{z},'
    pp = S + f'piece{i}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-ss', str(a), '-t', str(b - a), '-i', SRC,
                    '-vf', f'{crop}scale=1080:1920,setsar=1,fps=30', '-af', f'afade=t=in:d=0.02,afade=t=out:st={b-a-0.03}:d=0.03,aresample=48000',
                    '-ac', '2', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', pp], check=True)
    pieces.append(pp)
open(S + 'list.txt', 'w').write(''.join(f"file '{p}'\n" for p in pieces))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', S + 'list.txt', '-c', 'copy', S + 'cut.mp4'], check=True)
SRC = S + 'cut.mp4'
fc = []
fc.append('[0:v]null[vc]'); fc.append('[0:a]anull[ac]')
fc.append(f'[vc]eq=saturation=1.08:contrast=1.04,subtitles={S}story.ass:fontsdir=/root/.fonts[vs]')
inputs = ['-i', SRC]
cur = 'vs'
imgs = [('g_title.png', 0, TOTAL, '(W-w)/2', '250')] + [(f, s, e, '50', '1080') for f, s, e in W]
for j, (f, s, e, x, y) in enumerate(imgs):
    inputs += ['-loop', '1', '-t', str(TOTAL), '-i', S + f]
    k = j + 1
    fc.append(f'[{k}:v]format=rgba,fade=t=in:st={s}:d=0.25:alpha=1,fade=t=out:st={max(s, e-0.25)}:d=0.25:alpha=1[o{k}]')
    fc.append(f"[{cur}][o{k}]overlay=x={x}:y={y}:enable='between(t,{s},{e})'[x{k}]")
    cur = f'x{k}'
n = len(imgs) + 1
inputs += ['-f', 'lavfi', '-t', str(END), '-i', 'color=c=black:s=1080x1920:r=30',
           '-loop', '1', '-t', str(END), '-i', S + 'g_end.png',
           '-f', 'lavfi', '-t', str(END), '-i', 'anullsrc=r=48000:cl=stereo']
fc.append(f'[{n}:v][{n+1}:v]overlay=0:0,format=yuv420p,setsar=1[ev]')
fc.append(f'[{cur}]format=yuv420p[mv]')
fc.append(f'[ac]aresample=48000,aformat=channel_layouts=stereo[ma]')
fc.append(f'[mv][ma][ev][{n+2}:a]concat=n=2:v=1:a=1[vo][ao]')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[vo]', '-map', '[ao]',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p',
                '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', OUT], check=True)
print('OK', round(TOTAL + END, 2), OUT)
