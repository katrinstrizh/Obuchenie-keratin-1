import subprocess, sys
sys.path.insert(0, '/home/claude/asr')
import overlays as O

OUT = '/home/claude/out/'
name = '01_konsultaciya_3_voprosa'
tmp = OUT + 'tmp_' + name + '/'
ass = OUT + name + '.ass'
import sys as _s
VER=_s.argv[1]
CFG={'B':dict(title='Обучение кератину: 3 вопроса клиентке',hook='Делаешь кератин без этих 3 вопросов?',cx=0.56,grade=''),
     'C':dict(title='Почему не получается кератин?',hook='Кератин испортили? Ошибка была ДО утюжка',cx=0.50,grade=',eq=saturation=1.08:contrast=1.04,colorbalance=rs=0.03:bs=-0.02')}[VER]
D = 26.90; TAIL = 1.5; T = D + TAIL

# zoom keyframes by segment (output time): start, end, z_from, z_to
Z = [(0, 8.79, 1.00, 1.10), (8.79, 12.06, 1.20, 1.24), (12.06, 18.87, 1.00, 1.06),
     (18.87, 25.53, 1.16, 1.22), (25.53, 40, 1.32, 1.34)]
def zexpr():
    e = '1'
    for a, b, z0, z1 in reversed(Z):
        e = f"if(between(it,{a},{b}),{z0}+({z1}-{z0})*(it-{a})/({b}-{a}),{e})"
    return e.replace('it', '(in/30)')
CX, CY = None, 0.36

O.title_png(CFG['title'], tmp + 'title.png'); O.hook_png(CFG['hook'], tmp + 'hook.png')
O.name_brand_png(tmp + 'nameb.png')
O.card_png('1', 'Объём волос', tmp + 'c1.png')
O.card_png('2', 'Толщина волоса', tmp + 'c2.png')
O.card_png('3', 'Осветление, химия, нанопластика', tmp + 'c3.png')
O.neon_end_png(tmp + 'neon.png')

z = zexpr(); CX = CFG['cx']
cards = [(1, 8.85, 660), (2, 12.12, 790), (3, 18.95, 920)]
fc = [f"[0:v]tpad=stop_mode=add:stop_duration={TAIL}:color=black,zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{CX}*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{CY}*ih-ih/zoom/2))':d=1:s=1080x1920:fps=30,"
      f"subtitles={ass}{CFG['grade']}[b0]",
      f"[1:v]format=rgba,fade=in:st=0.15:d=0.35:alpha=1[ti]",
      f"[2:v]format=rgba,fade=in:st=4.0:d=0.3:alpha=1,fade=out:st=6.8:d=0.3:alpha=1[nm]",
      f"[6:v]format=rgba,fade=in:st={D:.2f}:d=0.25:alpha=1[en]",
      f"[b0][ti]overlay=0:120:enable='lt(t,{D})'[b1]",
      f"[b1][nm]overlay=W-w-20:320:enable='between(t,4.0,7.1)'[b2]"]
last = 'b2'
for i, (n, st, y) in enumerate(cards):
    fc.append(f"[{2+n}:v]format=rgba,fade=in:st={st}:d=0.3:alpha=1,fade=out:st=25.45:d=0.3:alpha=1[k{n}]")
    fc.append(f"[{last}][k{n}]overlay=W-w-50:{y}:enable='between(t,{st},25.8)'[c{n}]"); last = f'c{n}'
fc.append(f"[7:v]format=rgba,fade=out:st=2.0:d=0.3:alpha=1[hk]")
fc.append(f"[{last}][hk]overlay=0:640:enable='lt(t,2.3)'[h1]")
fc.append(f"[h1][en]overlay=0:0:enable='gte(t,{D})'[vo]")
fc.append(f"[0:a]loudnorm=I=-14:TP=-1.5,apad=pad_dur={TAIL}[ao]")
inputs = ['-f', 'concat', '-safe', '0', '-i', tmp + 'list.txt']
for p in ['title.png', 'nameb.png', 'c1.png', 'c2.png', 'c3.png', 'neon.png', 'hook.png']:
    inputs += ['-loop', '1', '-t', f'{T:.2f}', '-i', tmp + p]
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[vo]', '-map', '[ao]',
                '-t', f'{T:.2f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '30',
                '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', OUT + f'01{VER}_test.mp4'], check=True)
print('ok')
