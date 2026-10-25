"""До/после со щелчком: python3 snap.py <ver> <do.mov> <snap_do> <posle.mov> <snap_posle> <title> <hook> <out>"""
import sys, subprocess
sys.path.insert(0,'/home/claude/asr'); import overlays as O
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ver,do,sd,po,sp,title,hook,out=sys.argv[1],sys.argv[2],float(sys.argv[3]),sys.argv[4],float(sys.argv[5]),sys.argv[6],sys.argv[7],sys.argv[8]
T='/home/claude/out/snap/'+ver+'_'
PRE=2.0; POST=8.5; TAIL=1.5; D=PRE+POST; TT=D+TAIL
def chip(text,path,size=46):
    f=ImageFont.truetype(O.F+'Black.ttf',size); d=ImageDraw.Draw(Image.new('RGBA',(9,9)))
    pw=int(d.textlength(text,font=f))+60; ph=size+34
    img=Image.new('RGBA',(pw+30,ph+30),(0,0,0,0)); g=O.gradient(pw,ph).convert('RGBA'); m=Image.new('L',(pw,ph),0)
    ImageDraw.Draw(m).rounded_rectangle([0,0,pw-1,ph-1],22,fill=255); img.paste(g,(15,15),m)
    ImageDraw.Draw(img).text((45,15+13),text,font=f,fill='white'); img.save(path)
def card(lines,path,W=1080):
    f1=ImageFont.truetype(O.F+'Black.ttf',54); f2=ImageFont.truetype(O.F+'ExtraBold.ttf',40)
    d=ImageDraw.Draw(Image.new('RGBA',(9,9)))
    L=[(l,f1,(33,232,215)) for l in O.wrap(d,lines[0],f1,900)]+[(l,f2,(255,255,255)) for l in O.wrap(d,lines[1],f2,900)]
    hs=[66 if f is f1 else 52 for _,f,_ in L]; ph=sum(hs)+60; pw=960
    img=Image.new('RGBA',(W,ph+40),(0,0,0,0)); x0=(W-pw)//2
    gl=Image.new('RGBA',img.size,(0,0,0,0)); ImageDraw.Draw(gl).rounded_rectangle([x0,20,x0+pw,20+ph],34,fill=(24,212,178,160))
    img=Image.alpha_composite(img,gl.filter(ImageFilter.GaussianBlur(14)))
    dr=ImageDraw.Draw(img); dr.rounded_rectangle([x0,20,x0+pw,20+ph],34,fill=(6,38,34,238)); y=20+30
    for (l,f,c),h in zip(L,hs):
        tw=dr.textlength(l,font=f); dr.text(((W-tw)/2,y),l,font=f,fill=c); y+=h
    img.save(path)
O.title_png(title,T+'title.png'); O.name_brand_png(T+'name.png'); O.neon_end_png(T+'neon.png'); O.hook_png(hook,T+'hook.png')
chip('ДО',T+'do.png'); chip('ПОСЛЕ',T+'posle.png')
card(['Посмотрите, какие идеальные концы',''],T+'konc.png')
card(['ХОЧЕШЬ ТАК НАУЧИТЬСЯ? НАПИШИ МНЕ. ОНЛАЙН.','КАК ДЕЛАТЬ КЕРАТИН ТАК, ПРИ ЭТОМ БЫСТРО: ОНЛАЙН 1000 РУБ. (для опытных мастеров)'],T+'cta.png')
V='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1'
pngs=['title','name','neon','hook','do','posle','konc','cta']
inp=['-ss',f'{sd-PRE+0.04:.3f}','-t',f'{PRE:.3f}','-i',do,'-ss',f'{sp+0.06:.3f}','-t',f'{POST:.3f}','-i',po,'-f','lavfi','-t',f'{TT}','-i','color=white:s=1080x1920:r=30']
for p in pngs: inp+=['-loop','1','-t',f'{TT:.2f}','-i',T+p+'.png']
C=D-4.2  # старт призыва
fc=[f"[0:v]{V},eq=saturation=0.95[v0]",f"[1:v]{V},eq=saturation=1.06:contrast=1.03,zoompan=z='1.0+0.05*on/{POST*30:.0f}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30[v1]",
 "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[cv][ca]", f"[cv]tpad=stop_mode=add:stop_duration={TAIL}:color=black[bv]",
 f"[2:v]format=rgba,fade=in:st={PRE-0.02:.2f}:d=0.02:alpha=1,fade=out:st={PRE:.2f}:d=0.18:alpha=1[fl]",
 "[3:v]format=rgba,fade=in:st=0.1:d=0.3:alpha=1[ti]","[4:v]format=rgba,fade=in:st=2.4:d=0.25:alpha=1,fade=out:st=3.95:d=0.25:alpha=1[nm]",
 f"[5:v]format=rgba,fade=in:st={D:.2f}:d=0.25:alpha=1[en]","[6:v]format=rgba[hk]","[7:v]format=rgba[cd]","[8:v]format=rgba[cp]",
 f"[9:v]format=rgba,fade=in:st=4.3:d=0.3:alpha=1[kc]",f"[10:v]format=rgba,fade=in:st={C:.2f}:d=0.3:alpha=1[ct]",
 f"[bv][fl]overlay=0:0[b1]",f"[b1][ti]overlay=0:110:enable='lt(t,{D:.2f})'[b2]",f"[b2][cd]overlay=40:300:enable='lt(t,{PRE:.2f})'[b3]",
 f"[b3][cp]overlay=40:300:enable='between(t,{PRE:.2f},{D:.2f})'[b4]",f"[b4][hk]overlay=0:760:enable='lt(t,{PRE-0.05:.2f})'[b5]",
 f"[b5][nm]overlay=W-w-20:300:enable='between(t,2.4,4.2)'[b6]",f"[b6][kc]overlay=0:400:enable='between(t,4.3,{C:.2f})'[b7]",
 f"[b7][ct]overlay=0:400:enable='between(t,{C:.2f},{D:.2f})'[b8]",f"[b8][en]overlay=0:0:enable='gte(t,{D:.2f})'[vo]",
 f"[ca]loudnorm=I=-14:TP=-1.5,apad=pad_dur={TAIL}[ao]"]
subprocess.run(['ffmpeg','-v','error','-y','-threads','3']+inp+['-filter_complex',';'.join(fc),'-map','[vo]','-map','[ao]','-t',f'{TT:.2f}',
 '-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',out],check=True)
print(out,TT)
