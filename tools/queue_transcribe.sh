#!/bin/sh
# single-worker transcription queue; create /home/claude/work/PAUSE to pause between files
cd /home/claude/asr
for f in $(ls src/*.mov | sed 's#src/##;s#\.mov##' | grep -v -E '_[23]$|IMG_(6202|6203|6207|6208|6209|6210|6211|6212|6213|6214)_1$' | sort); do
  [ -f seg/$f.json ] && continue
  while [ -f /home/claude/work/PAUSE ]; do sleep 10; done
  python3 seg.py src/$f.mov seg/$f.json > seg/$f.txt 2>&1
done
echo ALLDONE > /home/claude/work/runner.done
