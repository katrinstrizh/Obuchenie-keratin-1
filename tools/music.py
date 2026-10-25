"""Синтез фирменного трека: нарастание -> удар на щелчке (t=hit) -> бит. python3 music.py out.wav hit total [bpm] [key]"""
import sys, numpy as np, wave
out,hit,total=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]); bpm=float(sys.argv[4]) if len(sys.argv)>4 else 108; root=float(sys.argv[5]) if len(sys.argv)>5 else 220.0
SR=44100; N=int(total*SR); t=np.arange(N)/SR; y=np.zeros(N); rng=np.random.default_rng(7)
def add(sig,t0):
    i=int(t0*SR); 
    if i>=N: return
    s=sig[:N-i]; y[i:i+len(s)]+=s
def env(n,a,d): x=np.arange(n)/SR; return np.minimum(x/a,1)*np.exp(-x/d)
def tone(f,dur,a=0.005,d=0.25,w='sin'):
    x=np.arange(int(dur*SR))/SR; s=np.sin(2*np.pi*f*x)+0.3*np.sin(4*np.pi*f*x)+(0.15*np.sin(6*np.pi*f*x))
    return s*env(len(x),a,d)
# нарастание до щелчка
n=int(hit*SR); x=np.arange(n)/SR; k=(x/hit)
f=300*(1+3*k**2); ph=2*np.pi*np.cumsum(f)/SR
ris=np.sin(ph)*0.18*k**2; noi=np.convolve(rng.normal(size=n),np.ones(6)/6,'same')*0.25*k**3
ris=ris+noi; ris[int((hit-0.04)*SR):]=0   # короткая пауза перед ударом
y[:n]+=ris
# удар
kx=np.arange(int(1.2*SR))/SR; kick=np.sin(2*np.pi*(50+120*np.exp(-kx*18))*kx)*np.exp(-kx*3.5)*1.0
add(kick,hit); add(rng.normal(size=int(0.5*SR))*np.exp(-np.arange(int(0.5*SR))/SR*9)*0.3,hit)
# блестящий аккорд (мажор-пентатоника) на удар
for m,fr in enumerate([1,1.25,1.5,2,2.5]): add(tone(root*fr*2,2.4,0.003,0.9)*0.10,hit+m*0.045)
# бит
beat=60/bpm; chords=[(1,1.25,1.5),(0.89,1.12,1.33),(0.75,0.94,1.12),(0.84,1.06,1.26)]
tt=hit; bar=0
while tt<total:
    c=chords[(bar//1)%4]
    for fr in c: add(tone(root*fr,beat*4,0.05,2.5)*0.05,tt)
    for q in range(4):
        b=tt+q*beat
        if b<total:
            add(kick[:int(0.35*SR)]*0.55,b)
            add(rng.normal(size=int(0.05*SR))*np.exp(-np.arange(int(0.05*SR))/SR*60)*0.12,b+beat/2)   # хэт
            add(tone(root*c[q%3]*2,beat,0.004,0.16)*0.07,b+beat/2)   # пингующая нота
    tt+=beat*4; bar+=1
fade=np.clip((total-t)/1.2,0,1); y*=fade
y=np.tanh(y*1.4)*0.8
w=wave.open(out,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y*32767).astype(np.int16).tobytes()); w.close()
