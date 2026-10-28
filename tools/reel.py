import subprocess, os, sys, re, json
sys.path.insert(0, '/home/claude/asr')
import overlays as O

SRC = '/home/claude/asr/src/'
OUT = '/home/claude/out/'
os.makedirs(OUT, exist_ok=True)
PAD_A, PAD_B = 0.03, 0.05   # padding around cuts (cuts are made at micro-pauses)
TAIL = 1.5

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat ExtraBold,70,&H00FFFFFF,&H00FFFFFF,&H00666E11,&H80000000,0,0,0,0,100,100,0,0,1,7,2,2,70,70,MV,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
HL = r'{\c&H00D7E821&}'; WH = r'{\c&H00FFFFFF&}'


def cards(text, maxlen=22):
    out, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > maxlen: out.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: out.append(cur)
    return out


def ts(t): return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'


def highlight(card, kws):
    res = []
    for w in card.split():
        core = re.sub(r'[^\wё+]', '', w.lower())
        hit = any(core.startswith(k.lower()[:max(4, len(k) - 2)]) for k in kws)
        res.append(HL + w + WH if hit else w)
    return ' '.join(res)


def cut_pieces(name, segs):
    tmp = OUT + 'tmp_' + name + '/'; os.makedirs(tmp, exist_ok=True)
    events, t = [], 0.0
    with open(tmp + 'list.txt', 'w') as lst:
        for i, (f, s, e, text) in enumerate(segs):
            a, b = max(0, s - PAD_A), e + PAD_B; d = b - a; p = f'{tmp}p{i}.mov'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-ss', f'{a:.3f}', '-i', SRC + f + '.mov', '-t', f'{d:.3f}',
                            '-vf', 'scale=1080:1920,fps=30', '-af', f'aresample=48000,afade=t=in:d=0.03,afade=t=out:st={d-0.03:.3f}:d=0.03',
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'pcm_s16le', p], check=True)
            lst.write(f"file '{p}'\n")
            cs = cards(text); total = sum(len(c) for c in cs); cur = t + (s - a)
            for c in cs:
                dd = (e - s) * len(c) / total; events.append((cur, cur + dd, c)); cur += dd
            events.append(None) if False else None
            t += d
    return tmp, events, t


def zexpr(bounds, cfg):
    # alternate gentle push-in segments; "punch" jump at each cut
    e = '1'; k = 0
    for (a, b) in reversed(bounds):
        pass
    parts = []
    for i, (a, b) in enumerate(bounds):
        z0, z1 = (1.00, 1.07) if i % 2 == 0 else (1.13, 1.20)
        z0 *= cfg.get('zs', 1.0); z1 *= cfg.get('zs', 1.0)
        parts.append((a, b, z0, z1))
    e = '1'
    for a, b, z0, z1 in reversed(parts):
        e = f"if(between(it,{a:.3f},{b:.3f}),{z0}+({z1}-{z0})*(it-{a:.3f})/({b-a:.3f}),{e})"
    return e.replace('it', '(in/30)')


def render(name, tmp, events, D, bounds, kws, ver, cfg, out_path):
    T = D + TAIL
    ass = OUT + f'{name}{ver}.ass'
    with open(ass, 'w', encoding='utf-8') as f:
        f.write(ASS_HEAD.replace(',MV,1', f",{cfg.get('mv', 400)},1"))
        for a, b, c in events: f.write(f'Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{highlight(c, kws)}\n')
    O.title_png(cfg['title'], tmp + f'title{ver}.png'); O.name_brand_png(tmp + 'nameb.png'); O.neon_end_png(tmp + 'neon.png')
    hook = cfg.get('hook')
    if hook: O.hook_png(hook, tmp + f'hook{ver}.png')
    z = zexpr(bounds, cfg); CX, CY = cfg.get('cx', 0.45), cfg.get('cy', 0.34)
    grade = cfg.get('grade', '')
    fc = [f"[0:v]tpad=stop_mode=add:stop_duration={TAIL}:color=black,zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{CX}*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{CY}*ih-ih/zoom/2))':d=1:s=1080x1920:fps=30,"
          f"subtitles={ass}{grade}[b0]",
          "[1:v]format=rgba,fade=in:st=0.15:d=0.35:alpha=1[ti]",
          "[2:v]format=rgba,fade=in:st=4.0:d=0.3:alpha=1,fade=out:st=6.8:d=0.3:alpha=1[nm]",
          f"[3:v]format=rgba,fade=in:st={D:.2f}:d=0.25:alpha=1[en]",
          f"[b0][ti]overlay=0:120:enable='lt(t,{D:.2f})'[b1]",
          "[b1][nm]overlay=W-w-20:320:enable='between(t,4.0,7.1)'[b2]"]
    last = 'b2'; inputs_png = [tmp + f'title{ver}.png', tmp + 'nameb.png', tmp + 'neon.png']
    if hook:
        inputs_png.append(tmp + f'hook{ver}.png')
        fc.append("[4:v]format=rgba,fade=out:st=2.0:d=0.3:alpha=1[hk]")
        fc.append(f"[{last}][hk]overlay=0:640:enable='lt(t,2.3)'[h1]"); last = 'h1'
    fc.append(f"[{last}][en]overlay=0:0:enable='gte(t,{D:.2f})'[vo]")
    fc.append(f"[0:a]loudnorm=I=-14:TP=-1.5,apad=pad_dur={TAIL}[ao]")
    inputs = ['-f', 'concat', '-safe', '0', '-i', tmp + 'list.txt']
    for p in inputs_png: inputs += ['-loop', '1', '-t', f'{T:.2f}', '-i', p]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[vo]', '-map', '[ao]',
                    '-t', f'{T:.2f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-maxrate', '3200k', '-bufsize', '6400k', '-pix_fmt', 'yuv420p', '-r', '30',
                    '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out_path], check=True)
    return T


def build_reel(name, segs, kws, versions, only=None):
    tmp, events, D = cut_pieces(name, segs)
    bounds, t = [], 0.0
    for (f, s, e, _) in segs:
        d = (e + PAD_B) - max(0, s - PAD_A); bounds.append((t, t + d)); t += d
    res = {}
    for ver, cfg in versions.items():
        if only and ver not in only: continue
        res[ver] = render(name, tmp, events, D, bounds, kws, ver, cfg, OUT + f'{name}_{ver}.mp4')
        print(name, ver, round(res[ver], 1), flush=True)
    return res


if __name__ == '__main__':
    import importlib.util
    spec = importlib.util.spec_from_file_location('reels', os.environ.get('REELCFG', '/home/claude/work/reels_cfg.py')); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    want = sys.argv[1:]
    for name, (segs, kws, versions) in m.REELS.items():
        names = [w for w in want if w not in ('A', 'B', 'C')]
        if names and not any(name.startswith(w) for w in names): continue
        vs = [w for w in want if w in ('A', 'B', 'C')] or None
        build_reel(name, segs, kws, versions, vs)
