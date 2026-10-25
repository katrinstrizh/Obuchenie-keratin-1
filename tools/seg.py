import sys, re, subprocess, json
import transcribe as T
path=sys.argv[1]; a=T.load_audio(path); dur=len(a)/T.SR
r=subprocess.run(['ffmpeg','-i',path,'-af','dynaudnorm=f=200:g=15,silencedetect=noise=-30dB:d=0.25','-f','null','-'],capture_output=True,text=True).stderr
S=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',r)]; E=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',r)]
sil=list(zip(S,E))
# speech islands between silences
isl=[]; cur=0.0
for s,e in sil:
    if s-cur>0.15: isl.append([cur,s])
    cur=e
if dur-cur>0.15: isl.append([cur,dur])
# merge islands separated by <0.25 and keep <=8s
m=[]
for s,e in isl:
    if m and s-m[-1][1]<0.25 and e-m[-1][0]<8: m[-1][1]=e
    else: m.append([s,e])
out=[]
for i,(s,e) in enumerate(m):
    ps,pe=max(0,s-0.1),min(dur,e+0.1)
    t=T.decode_chunk(a[int(ps*T.SR):int(pe*T.SR)]) if pe-ps>0.3 else ''
    if 'Продолжение следует' in t or 'Субтитры' in t: t='(—)'
    out.append({'i':i,'s':round(s,2),'e':round(e,2),'t':t}); print(f"{i:3d} {s:6.2f}-{e:6.2f} {t}",flush=True)
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
