# Накладывает крупный хук по центру (0–2,3 с) на версии А: videos/NNA_*_h2.mp4 -> NNA_*_h3.mp4
import sys, os, glob, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import patch_hooks as P
from hooks_a import HA

V = '/home/claude/obuchenie-keratin-1/videos/'
TMP = '/tmp/claude-0/-home-claude/4edc9c36-bbfd-56a0-b2f5-53f02e4ef983/scratchpad/ha/'
os.makedirs(TMP, exist_ok=True)
only = [int(x) for x in sys.argv[1:]] or sorted(HA)
for n in only:
    src = glob.glob(V + f'{n:02d}A_*_h2.mp4')[0]
    dst = src.replace('_h2.mp4', '_h3.mp4')
    if os.path.exists(dst): print('skip', dst); continue
    w, h, lines = P.hook_dims(HA[n]); assert len(lines) <= 3, (n, lines)
    png = TMP + f'h{n}.png'; P.hook_png(HA[n], None, png)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-i', src, '-i', png, '-filter_complex',
                    "[0:v][1:v]overlay=0:640:enable='lt(t,2.3)'[v]", '-map', '[v]', '-map', '0:a',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'copy', '-movflags', '+faststart', dst], check=True)
    print('ok', os.path.basename(dst), os.path.getsize(dst) // 1048576, 'MB')
