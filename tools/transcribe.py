import sys, json, base64, subprocess, re
import numpy as np, onnxruntime as ort

M = '/home/claude/sherpa-onnx-whisper-turbo/'
SR = 16000

def load_audio(path):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af', 'dynaudnorm=f=200:g=15', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32).copy()

def mel_filters(n_mels=128, n_fft=400, sr=SR):
    def hz2mel(f):
        f = np.asanyarray(f, dtype=float)
        mels = f / (200.0 / 3)
        min_log_hz, min_log_mel, logstep = 1000.0, 15.0, np.log(6.4) / 27.0
        return np.where(f >= min_log_hz, min_log_mel + np.log(np.maximum(f, 1e-10) / min_log_hz) / logstep, mels)
    def mel2hz(m):
        m = np.asanyarray(m, dtype=float)
        f = (200.0 / 3) * m
        min_log_hz, min_log_mel, logstep = 1000.0, 15.0, np.log(6.4) / 27.0
        return np.where(m >= min_log_mel, min_log_hz * np.exp(logstep * (m - min_log_mel)), f)
    fftfreqs = np.linspace(0, sr / 2, 1 + n_fft // 2)
    mel_f = mel2hz(np.linspace(hz2mel(0), hz2mel(sr / 2), n_mels + 2))
    fdiff = np.diff(mel_f)
    ramps = mel_f[:, None] - fftfreqs[None, :]
    w = np.zeros((n_mels, len(fftfreqs)))
    for i in range(n_mels):
        lower = -ramps[i] / fdiff[i]
        upper = ramps[i + 2] / fdiff[i + 1]
        w[i] = np.maximum(0, np.minimum(lower, upper))
    enorm = 2.0 / (mel_f[2:n_mels + 2] - mel_f[:n_mels])
    w *= enorm[:, None]
    return w.astype(np.float32)

FB = mel_filters()
WIN = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(400) / 400)).astype(np.float32)

def log_mel(audio):
    audio = np.pad(audio, (0, max(0, SR * 30 - len(audio))))[:SR * 30]
    x = np.pad(audio, (200, 200), mode='reflect')
    n = 1 + (len(x) - 400) // 160
    frames = np.lib.stride_tricks.as_strided(x, (n, 400), (x.strides[0] * 160, x.strides[0])) * WIN
    mag = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    mag = mag[:-1]
    mel = FB @ mag.T
    lm = np.log10(np.maximum(mel, 1e-10))
    lm = np.maximum(lm, lm.max() - 8.0)
    return ((lm + 4.0) / 4.0).astype(np.float32)[None]

enc = ort.InferenceSession(M + 'turbo-encoder.int8.onnx', providers=['CPUExecutionProvider'])
dec = ort.InferenceSession(M + 'turbo-decoder.int8.onnx', providers=['CPUExecutionProvider'])
meta = enc.get_modelmeta().custom_metadata_map
codes = meta['all_language_codes'].split(',')
ltoks = [int(t) for t in meta['all_language_tokens'].split(',')]
LANG = dict(zip(codes, ltoks))
EOT = int(meta['eot'])
SOT = int(meta['sot']); TRANSCRIBE = int(meta['transcribe']); NOTS = int(meta['no_timestamps'])
vocab = {}
for line in open(M + 'turbo-tokens.txt', encoding='utf-8'):
    p = line.rstrip('\n').split(' ')
    if len(p) == 2:
        vocab[int(p[1])] = base64.b64decode(p[0])

def decode_chunk(audio, lang='ru'):
    k, v = enc.run(None, {'mel': log_mel(audio)})
    sk = np.zeros((4, 1, 448, 1280), np.float32); sv = np.zeros_like(sk)
    toks = [SOT, LANG[lang], TRANSCRIBE, NOTS]
    feed = np.array([toks], np.int64); offset = 0; out = []
    for _ in range(220):
        logits, sk, sv = dec.run(None, {'tokens': feed, 'in_n_layer_self_k_cache': sk, 'in_n_layer_self_v_cache': sv,
                                        'n_layer_cross_k': k, 'n_layer_cross_v': v, 'offset': np.array([offset], np.int64)})
        offset += feed.shape[1]
        lg = logits[0, -1]
        lg[EOT + 1:] = -np.inf if len(out) == 0 else lg[EOT + 1:]
        lg[EOT + 1:] = -np.inf
        t = int(np.argmax(lg))
        if t == EOT: break
        out.append(t)
        if len(out) > 30 and out[-10:] == out[-20:-10]: break
        feed = np.array([[t]], np.int64)
    return b''.join(vocab.get(t, b'') for t in out).decode('utf-8', 'replace').strip()

def chunks(path, audio):
    dur = len(audio) / SR
    r = subprocess.run(['ffmpeg', '-i', path, '-af', 'dynaudnorm=f=200:g=15,silencedetect=noise=-30dB:d=0.35', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    cuts = [(s + e) / 2 for s, e in zip(starts, ends)]
    segs, cur = [], 0.0
    while cur < dur - 0.3:
        cands = [c for c in cuts if cur + 3 < c <= cur + 12]
        nxt = cands[-1] if cands else min(cur + 12, dur)
        if dur - nxt < 2: nxt = dur
        segs.append((cur, nxt)); cur = nxt
    return segs

def fmt(s):
    return f'{int(s // 60)}:{s % 60:04.1f}'

if __name__ == '__main__':
    res = {}
    for path in sys.argv[1:]:
        a = load_audio(path)
        lines = []
        for s, e in chunks(path, a):
            txt = decode_chunk(a[int(s * SR):int(e * SR)])
            lines.append({'start': round(s, 1), 'end': round(e, 1), 'text': txt})
            print(f'[{fmt(s)}–{fmt(e)}] {txt}', flush=True)
        res[path] = lines
        print('----', flush=True)
    json.dump(res, open('/home/claude/asr/out.json', 'w'), ensure_ascii=False, indent=1)
