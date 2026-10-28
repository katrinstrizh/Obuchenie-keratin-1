#!/bin/sh
# usage: dips.sh file start end  -> micro pauses (absolute time)
ffmpeg -ss $2 -t $(echo "$3 - $2" | bc) -i /home/claude/asr/src/$1.mov -af "dynaudnorm=f=200:g=15,silencedetect=noise=-26dB:d=0.06" -f null - 2>&1 | grep -oE "silence_(start|end): [0-9.]+" | awk -v o=$2 '/start/{s=$2+o} /end/{printf "%.2f-%.2f ", s, $2+o}'
echo
