# FFmpeg Production Playbook

## 1. 9:16 Vertical Video Adaptation with Blurred Ambient Background
```bash
ffmpeg -y -i input.mp4 -filter_complex \
  "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg]; \
   [0:v]scale=1080:-2[fg]; \
   [bg][fg]overlay=(W-w)/2:(H-h)/2[v]" \
  -map "[v]" -c:v libx264 -preset fast -crf 20 -c:a copy output_916.mp4
```

## 2. Picture-in-Picture (PiP) Layering with Drop Shadow & Rounded Corners
```bash
ffmpeg -y -i background.mp4 -i talking_head.mp4 -filter_complex \
  "[1:v]scale=400:400,format=yuva420p[pip]; \
   [0:v][pip]overlay=W-w-50:H-h-120:format=auto[outv]" \
  -map "[outv]" -c:v libx264 -crf 21 output_pip.mp4
```

## 3. Automated Audio Ducking (Voiceover vs Background Music)
```bash
ffmpeg -y -i speech.mp3 -i music.mp3 -filter_complex \
  "[1:a]volume=0.25[bgm]; \
   [0:a][bgm]sidechaincompress=threshold=0.15:ratio=4:attack=20:release=300[outa]" \
  -map 0:v -map "[outa]" -c:v copy -c:a aac -b:a 192k final_ducked.mp4
```

## 4. EBU R128 Loudness Normalization (-14 LUFS for YouTube / -16 LUFS for Reels)
```bash
ffmpeg -y -i input.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11" normalized_voice.wav
```
