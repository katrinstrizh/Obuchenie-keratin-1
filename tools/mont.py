"""Монтаж «идеальные концы»: python3 mont.py <ver> <title> <hook> <out> <order e.g. 6274,6275,6277,6279>"""
import sys, subprocess
sys.path.insert(0,'/home/claude/asr'); import overlays as O
exec(open('/home/claude/asr/snapm.py').read().split("O.title_png")[0].split("def chip")[0].split("ver,do")[0])
src=open('/home/claude/asr/snapm.py').read()
ns={}; exec("import sys\nsys.path.insert(0,'/home/claude/asr')\nimport overlays as O\nfrom PIL import Image, ImageDraw, ImageFont, ImageFilter\n"+src[src.index("def chip"):src.index("O.title_png")],ns)
chip,card=ns['chip'],ns['card']
ver,title,hook,out,order=sys.argv[1:6]
T='/home/claude/out/snap/M'+ver+'_'
S='/home/claude/src/'; files={'6274':S+'p6274.mov','6275':S+'p6275.mov','6277':S+'p6277.mov','6279':S+'posle.mov'}
SEG=float(sys.argv[6]) if len(sys.argv)>6 else 3.4; ids=order.split(','); D=SEG*len(ids); TAIL=1.5; TT=D+TAIL
O.title_png(title,T+'title.png'); O.name_brand_png(T+'name.png'); O.neon_end_png(T+'neon.png'); O.hook_png(hook,T+'hook.png')
card(['Посмотрите, какие идеальные концы',''],T+'konc.png')
card(['ХОЧЕШЬ ТАК НАУЧИТЬСЯ? НАПИШИ МНЕ. ОНЛАЙН.','КАК ДЕЛАТЬ КЕРАТИН ТАК, ПРИ ЭТОМ БЫСТРО: ОНЛАЙН 1000 РУБ. (для опытных мастеров)'],T+'cta.png')
subprocess.run(['python3','/home/claude/asr/music.py',T+'mus.wav','0.5',str(TT),'104'],check=True)
V='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1'
inp=[]; 
for i in ids: inp+=['-ss','0.3' if i!='6279' else '0.6','-t',f'{SEG}','-i',files[i]]
n=len(ids); pngs=['title','name','neon','hook','konc','cta']
for p in pngs: inp+=['-loop','1','-t',f'{TT:.2f}','-i',T+p+'.png']
inp+=['-i',T+'mus.wav']
fc=[f"[{k}:v]{V},eq=saturation=1.05:contrast=1.03,zoompan=z='1.0+0.06*on/{SEG*30:.0f}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30[c{k}]" for k in range(n)]
fc.append(''.join(f'[c{k}]' for k in range(n))+f"concat=n={n}:v=1:a=0[cv]"); fc.append(f"[cv]tpad=stop_mode=add:stop_duration={TAIL}:color=black[bv]")
b=n; C=D-4.2
fc+= [f"[{b}:v]format=rgba,fade=in:st=0.1:d=0.3:alpha=1[ti]",f"[{b+1}:v]format=rgba,fade=in:st=2.4:d=0.25:alpha=1,fade=out:st=3.95:d=0.25:alpha=1[nm]",
 f"[{b+2}:v]format=rgba,fade=in:st={D:.2f}:d=0.25:alpha=1[en]",f"[{b+3}:v]format=rgba[hk]",f"[{b+4}:v]format=rgba,fade=in:st=4.3:d=0.3:alpha=1[kc]",f"[{b+5}:v]format=rgba,fade=in:st={C:.2f}:d=0.3:alpha=1[ct]",
 f"[bv][ti]overlay=0:110:enable='lt(t,{D:.2f})'[b2]",f"[b2][hk]overlay=0:760:enable='lt(t,2.0)'[b5]",f"[b5][nm]overlay=W-w-20:300:enable='between(t,2.4,4.2)'[b6]",
 f"[b6][kc]overlay=0:400:enable='between(t,4.3,{C:.2f})'[b7]",f"[b7][ct]overlay=0:400:enable='between(t,{C:.2f},{D:.2f})'[b8]",f"[b8][en]overlay=0:0:enable='gte(t,{D:.2f})'[vo]",
 f"[{b+6}:a]volume=0.9,alimiter=limit=0.95[ao]"]
subprocess.run(['ffmpeg','-v','error','-y','-threads','3']+inp+['-filter_complex',';'.join(fc),'-map','[vo]','-map','[ao]','-t',f'{TT:.2f}','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',out],check=True)
print(out,TT)
