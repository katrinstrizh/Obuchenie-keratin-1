import sys, os, json, subprocess
sys.path.insert(0,'/home/claude/obuchenie-keratin-1/tools')
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import overlays as O
F=O.F; W=1080

def title_dims(text):
    font=ImageFont.truetype(F+'ExtraBold.ttf',50); d=ImageDraw.Draw(Image.new('RGBA',(10,10)))
    lines=O.wrap(d,text,font,860); return int(max(d.textlength(l,font=font) for l in lines))+80, 62*len(lines)+44, lines

def hook_dims(text):
    font=ImageFont.truetype(F+'Black.ttf',74); d=ImageDraw.Draw(Image.new('RGBA',(10,10)))
    lines=O.wrap(d,text,font,880); return int(max(d.textlength(l,font=font) for l in lines))+90, 90*len(lines)+60, lines

def title_png(new, old, path):
    pw,ph,lines=title_dims(new); opw,oph,_=title_dims(old) if old else (0,0,0)
    pw=max(pw,opw+20); ph=max(ph,oph+16); top=0  # old plate top was 8
    font=ImageFont.truetype(F+'ExtraBold.ttf',50)
    canvas=Image.new('RGBA',(W,ph+48),(0,0,0,0)); x0=(W-pw)//2
    sh=Image.new('RGBA',canvas.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([x0,top+6,x0+pw,top+6+ph],30,fill=(0,40,35,110))
    canvas=Image.alpha_composite(canvas,sh.filter(ImageFilter.GaussianBlur(10)))
    g=O.gradient(pw,ph).convert('RGBA'); m=Image.new('L',(pw,ph),0); ImageDraw.Draw(m).rounded_rectangle([0,0,pw-1,ph-1],30,fill=255)
    canvas.paste(g,(x0,top),m); dr=ImageDraw.Draw(canvas)
    y0=top+(ph-62*len(lines))//2-4
    for i,l in enumerate(lines):
        tw=dr.textlength(l,font=font); dr.text(((W-tw)/2,y0+i*62),l,font=font,fill='white')
    canvas.save(path)

def hook_png(new, old, path):
    pw,ph,lines=hook_dims(new); opw,oph,_=hook_dims(old) if old else (0,0,0)
    pw=max(pw,opw+24); ph=max(ph,oph+20); top=10  # old plate top was 20
    font=ImageFont.truetype(F+'Black.ttf',74)
    img=Image.new('RGBA',(W,ph+70),(0,0,0,0)); x0=(W-pw)//2
    gl=Image.new('RGBA',img.size,(0,0,0,0)); ImageDraw.Draw(gl).rounded_rectangle([x0,top,x0+pw,top+ph],36,fill=(24,212,178,170))
    img=Image.alpha_composite(img,gl.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(img).rounded_rectangle([x0,top,x0+pw,top+ph],36,fill=(6,38,34,255)); dr=ImageDraw.Draw(img)
    y0=top+(ph-90*len(lines))//2-2
    for i,l in enumerate(lines):
        tw=dr.textlength(l,font=font); dr.text(((W-tw)/2,y0+i*90),l,font=font,fill=(33,232,215,255) if i==0 else (255,255,255,255))
    img.save(path)

def dur(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]).decode())

def patch(src,dst,old_title,new_title,old_hook,new_hook,tmp):
    T=dur(src); D=T-1.5
    os.makedirs(tmp,exist_ok=True); title_png(new_title,old_title,tmp+'t.png')
    inputs=['-i',src,'-i',tmp+'t.png']; fc=[f"[0:v][1:v]overlay=0:120:enable='lt(t,{D:.2f})'[v1]"]; last='v1'
    if new_hook:
        hook_png(new_hook,old_hook,tmp+'h.png'); inputs+=['-i',tmp+'h.png']
        fc.append(f"[{last}][2:v]overlay=0:640:enable='lt(t,2.3)'[v2]"); last='v2'
    subprocess.run(['ffmpeg','-v','error','-y','-threads','2']+inputs+['-filter_complex',';'.join(fc),'-map',f'[{last}]','-map','0:a','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',dst],check=True)

if __name__=='__main__':
    a=json.loads(sys.argv[1]); os.makedirs(a['tmp'],exist_ok=True)
    patch(a['src'],a['dst'],a.get('ot'),a['nt'],a.get('oh'),a.get('nh'),a['tmp'])
