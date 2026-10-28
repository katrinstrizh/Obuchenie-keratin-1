import sys, subprocess, numpy as np
sys.path.insert(0,'/home/claude/asr')
import transcribe as T
# usage: says.py file a-b [a-b ...]  -> text of each snippet
f=sys.argv[1]
for r in sys.argv[2:]:
    a,b=map(float,r.split('-'))
    out=subprocess.run(['ffmpeg','-v','error','-ss',str(a),'-t',str(b-a),'-i',f'/home/claude/asr/src/{f}.mov','-af','dynaudnorm=f=200:g=15','-ac','1','-ar','16000','-f','f32le','-'],capture_output=True).stdout
    x=np.frombuffer(out,np.float32).copy()
    print(f"{a:7.2f}-{b:7.2f} {T.decode_chunk(x)}",flush=True)
