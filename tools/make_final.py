"""Финальный рендер ролика: приближения, заголовок, плашка «Катя Стриж» (4–7 с), хук (версии B/C), неоновый финал 1,5 с.
Использование: python3 make_final.py <имя_клипа> <A|B|C>"""
import subprocess, sys, json
sys.path.insert(0, '/home/claude/asr')
import overlays as O

OUT = '/home/claude/out/'
CFG = json.load(open('/home/claude/asr/hooks.json', encoding='utf-8'))
name, ver = sys.argv[1], sys.argv[2]
c = CFG[name]; v = c[ver]
tmp = OUT + 'tmp_' + name + '/'
ass = OUT + name + '.ass'
parts = [l.split("'")[1] for l in open(tmp + 'list.txt') if l.strip()]
durs = [float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                             capture_output=True, text=True).stdout) for p in parts]
D = sum(durs); TAIL = 1.5; T = D + TAIL
# мягкие приближения: чётные части — плавный наезд, нечётные — «пробивка» крупнее
Z, t = [], 0.0
for i, d in enumerate(durs):
    zmax = c.get('zmax', 1.14)
    Z.append((t, t + d, 1.0, 1.06) if i % 2 == 0 else (t, t + d, zmax - 0.04, zmax)); t += d
Z.append((D, D + 10, 1.0, 1.0))
e = '1'
for a, b, z0, z1 in reversed(Z):
    e = f"if(between(it,{a:.3f},{b:.3f}),{z0}+({z1}-{z0})*(it-{a:.3f})/({b-a:.3f}),{e})"
z = e.replace('it', '(in/30)')
CX = v.get('cx', c.get('cx', 0.5)); CY = c.get('cy', 0.42)
grade = ',eq=saturation=1.08:contrast=1.04,colorbalance=rs=0.03:bs=-0.02' if ver == 'C' else ''

O.title_png(v['title'], tmp + f'title_{ver}.png'); O.name_brand_png(tmp + 'nameb.png'); O.neon_end_png(tmp + 'neon.png')
inputs = ['-f', 'concat', '-safe', '0', '-i', tmp + 'list.txt']
for p in [f'title_{ver}.png', 'nameb.png', 'neon.png']:
    inputs += ['-loop', '1', '-t', f'{T:.2f}', '-i', tmp + p]
fc = [f"[0:v]tpad=stop_mode=add:stop_duration={TAIL}:color=black,zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{CX}*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{CY}*ih-ih/zoom/2))':d=1:s=1080x1920:fps=30,subtitles={ass}{grade}[b0]",
      "[1:v]format=rgba,fade=in:st=0.15:d=0.35:alpha=1[ti]",
      "[2:v]format=rgba,fade=in:st=4.0:d=0.3:alpha=1,fade=out:st=6.8:d=0.3:alpha=1[nm]",
      f"[3:v]format=rgba,fade=in:st={D:.2f}:d=0.25:alpha=1[en]",
      f"[b0][ti]overlay=0:120:enable='lt(t,{D:.2f})'[b1]",
      "[b1][nm]overlay=W-w-20:320:enable='between(t,4.0,7.1)'[b2]"]
last = 'b2'
if v.get('hook'):
    O.hook_png(v['hook'], tmp + f'hook_{ver}.png')
    inputs += ['-loop', '1', '-t', f'{T:.2f}', '-i', tmp + f'hook_{ver}.png']
    fc += ["[4:v]format=rgba,fade=out:st=2.0:d=0.3:alpha=1[hk]", f"[b2][hk]overlay=0:640:enable='lt(t,2.3)'[b3]"]; last = 'b3'
fc += [f"[{last}][en]overlay=0:0:enable='gte(t,{D:.2f})'[vo]", f"[0:a]loudnorm=I=-14:TP=-1.5,apad=pad_dur={TAIL}[ao]"]
out = OUT + f'final/{name[:2]}{ver}_{name[3:]}.mp4'
subprocess.run(['mkdir', '-p', OUT + 'final'])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[vo]', '-map', '[ao]',
                '-t', f'{T:.2f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-r', '30',
                '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
print(out, round(T, 1))
