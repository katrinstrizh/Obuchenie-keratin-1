# Инструменты монтажа рилсов Кати Стриж

Рабочая среда Claude очищается между чатами, поэтому в новом чате сначала подготовить её:

```bash
# 1. Модель распознавания русской речи (Whisper turbo, ~560 МБ, качается с GitHub)
cd /home/claude && curl -sSL -o turbo.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2 && tar xjf turbo.tar.bz2
# 2. Фирменный шрифт Montserrat
GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/JulietaUla/montserrat /home/claude/julietaula/montserrat
mkdir -p ~/.fonts && cp /home/claude/julietaula/montserrat/fonts/ttf/Montserrat-{ExtraBold,Bold,SemiBold,Black}.ttf ~/.fonts/ && fc-cache -f
# 3. Скрипты
mkdir -p /home/claude/asr && cp /home/claude/obuchenie-keratin-1/tools/*.py /home/claude/asr/
```
onnxruntime, ffmpeg и Pillow уже установлены. pip до PyPI не достучится — он и не нужен.

## Файлы
- `transcribe.py` — расшифровка русской речи (load_audio, decode_chunk). `python3 transcribe.py видео.mov` → текст с таймкодами.
- `seg.py видео.mov out.json` — расшифровка по фразам между паузами (для поиска повторов и точек резки).
  Whisper «сглаживает» повторы: чтобы их найти, расшифровывать короткими кусками по микропаузам (silencedetect d=0.05) и проверять склейку.
- `edit.py` — нарезка по таймкодам (CLIPS: файл, заголовок, фразы с таймкодами, ключевые слова) → куски в /home/claude/out/tmp_<имя>/ и черновик.
- `overlays.py` — графика в фирменном стиле: заголовок-градиент, плашка «Катя Стриж», карточки с номерами, хук, неоновая финальная заставка.
- `make01v.py` — финальная сборка ролика (пример для видео 01): приближения zoompan, субтитры, плашки, карточки, хук, чёрный финал.
