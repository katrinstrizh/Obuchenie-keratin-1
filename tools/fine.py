import sys, re, subprocess
import transcribe as T
path=sys.argv[1]; S0=float(sys.argv[2]); E0=float(sys.argv[3])
a=T.load_audio(path)
seg=a[int(S0*T.SR):int(E0*T.SR)]
import numpy as np, tempfile, os
tmp='/tmp/fine.wav'
subprocess.run(['ffmpeg','-v','error','-y','-ss',str(S0),'-t',str(E0-S0),'-i',path,'-af','dynaudnorm=f=200:g=15','-ac','1',tmp],check=True)
r=subprocess.run(['ffmpeg','-i',tmp,'-af','silencedetect=noise=-32dB:d=0.12','-f','null','-'],capture_output=True,text=True).stderr
S=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',r)]; Eend=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',r)]
dur=E0-S0; isl=[]; cur=0.0
for s,e in zip(S,Eend):
    if s-cur>0.12: isl.append([cur,s])
    cur=e
if dur-cur>0.12: isl.append([cur,dur])
for s,e in isl:
    ps,pe=max(0,s-0.05),min(dur,e+0.05)
    t=T.decode_chunk(seg[int(ps*T.SR):int(pe*T.SR)]) if pe-ps>0.25 else ''
    print(f"{S0+s:7.2f}-{S0+e:7.2f} {t}",flush=True)
