"""До/после со щелчком: python3 make_ba.py <name> <do.mov> <do_start> <snap_end> <posle.mov> <posle_start> <posle_end> <A|B|C> <title> [hook]"""
import sys, subprocess
sys.path.insert(0,'/home/claude/asr'); import overlays as O
from PIL import Image, ImageDraw, ImageFont, ImageFilter
name,do,ds,de,po,ps,pe,ver,title=sys.argv[1:10]; hook=sys.argv[10] if len(sys.argv)>10 else ''
ds,de,ps,pe=map(float,(ds,de,ps,pe)); d1=de-ds; d2=pe-ps; D=d1+d2; TAIL=1.5; T=D+TAIL
tmp=f'/home/claude/ba/tmp_{name}_{ver}/'; subprocess.run(['mkdir','-p',tmp])
F=O.F
def tag(text,path):
    f=ImageFont.truetype(F+'Black.ttf',64); d=ImageDraw.Draw(Image.new('RGBA',(9,9))); w=int(d.textlength(text,font=f))+70
    img=Image.new('RGBA',(w+20,120),(0,0,0,0)); g=O.gradient(w,96).convert('RGBA'); m=Image.new('L',(w,96),0)
    ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,95],28,fill=255); img.paste(g,(10,12),m)
    ImageDraw.Draw(img).text((45,24),text,font=f,fill='white'); img.save(path)
def cta(path,W=1080):
    f1=ImageFont.truetype(F+'Black.ttf',58); f2=ImageFont.truetype(F+'ExtraBold.ttf',40); f3=ImageFont.truetype(F+'SemiBold.ttf',32)
    d=ImageDraw.Draw(Image.new('RGBA',(9,9)))
    L=[(O.wrap(d,'ХОЧЕШЬ ТАК НАУЧИТЬСЯ? НАПИШИ МНЕ «ОНЛАЙН»',f1,900),f1,72,(33,232,215)),
       (O.wrap(d,'КАК ДЕЛАТЬ КЕРАТИН ТАК, ПРИ ЭТОМ БЫСТРО: ОНЛАЙН 1000 ₽',f2,900),f2,52,(255,255,255)),
       (['(для опытных мастеров)'],f3,44,(200,240,235))]
    ph=sum(len(l)*lh for l,_,lh,_ in L)+80; img=Image.new('RGBA',(W,ph+40),(0,0,0,0))
    glow=Image.new('RGBA',img.size,(0,0,0,0)); ImageDraw.Draw(glow).rounded_rectangle([60,20,W-60,20+ph],36,fill=(24,212,178,170))
    img=Image.alpha_composite(img,glow.filter(ImageFilter.GaussianBlur(16))); dr=ImageDraw.Draw(img)
    dr.rounded_rectangle([60,20,W-60,20+ph],36,fill=(6,38,34,238)); y=20+38
    for lines,f,lh,col in L:
        for l in lines: tw=dr.textlength(l,font=f); dr.text(((W-tw)/2,y),l,font=f,fill=col); y+=lh
    img.save(path)
O.title_png(title,tmp+'title.png'); O.name_brand_png(tmp+'nameb.png'); O.neon_end_png(tmp+'neon.png')
tag('ДО',tmp+'do.png'); tag('ПОСЛЕ',tmp+'posle.png'); cta(tmp+'cta.png')
if hook: O.hook_png(hook,tmp+'hook.png')
cx=0.42 if ver=='C' else 0.5
grade=',eq=saturation=1.06:contrast=1.04' if ver=='C' else ''
# части: до (с щелчком, звук щелчка +4дБ), после — с «ударным» приближением 1.10→1.0 за 0.5 с
seg=lambda src,a,dur,out,extra: subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{a:.3f}','-i',src,'-t',f'{dur:.3f}','-vf','scale=1080:1920,fps=30'+extra,
    '-af','aresample=48000,volume=1.6','-c:v','libx264','-preset','veryfast','-crf','16','-pix_fmt','yuv420p','-c:a','pcm_s16le',out],check=True)
seg(do,ds,d1,tmp+'p0.mov',grade)
z="if(lt(in,15),1.10-0.10*in/15,1.0)"
seg(po,ps,d2,tmp+'p1.mov',f",zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30{grade}")
open(tmp+'list.txt','w').write(f"file '{tmp}p0.mov'\nfile '{tmp}p1.mov'\n")
ins=['-f','concat','-safe','0','-i',tmp+'list.txt']
for p in ['title','nameb','neon','do','posle','cta']+(['hook'] if hook else []): ins+=['-loop','1','-t',f'{T:.2f}','-i',tmp+p+'.png']
cs=D-3.2
fc=[f"[0:v]tpad=stop_mode=add:stop_duration={TAIL}:color=black[b0]",
    f"[b0][1:v]overlay=0:120:enable='lt(t,{D:.2f})'[b1]",
    "[2:v]format=rgba,fade=in:st=4.0:d=0.3:alpha=1,fade=out:st=6.8:d=0.3:alpha=1[nm]",
    "[b1][nm]overlay=W-w-20:320:enable='between(t,4.0,7.1)'[b2]",
    f"[b2][4:v]overlay=40:330:enable='lt(t,{d1:.2f})'[b3]",
    f"[b3][5:v]overlay=40:330:enable='between(t,{d1:.2f},{cs:.2f})'[b4]",
    f"[6:v]format=rgba,fade=in:st={cs:.2f}:d=0.3:alpha=1[ct]",
    f"[b4][ct]overlay=0:1180:enable='between(t,{cs:.2f},{D:.2f})'[b5]"]
last='b5'
if hook: fc+=["[7:v]format=rgba,fade=out:st=1.9:d=0.3:alpha=1[hk]",f"[b5][hk]overlay=0:700:enable='lt(t,2.2)'[b6]"]; last='b6'
fc+=[f"[3:v]format=rgba,fade=in:st={D:.2f}:d=0.25:alpha=1[en]",f"[{last}][en]overlay=0:0:enable='gte(t,{D:.2f})'[vo]",
     f"[0:a]loudnorm=I=-14:TP=-1.0,apad=pad_dur={TAIL}[ao]"]
out=f'/home/claude/out/final/{name[:3]}{ver}_{name[4:]}.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-threads','2']+ins+['-filter_complex',';'.join(fc),'-map','[vo]','-map','[ao]','-t',f'{T:.2f}',
    '-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','160k','-movflags','+faststart',out],check=True)
print(out,round(T,1))
