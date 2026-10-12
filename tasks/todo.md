# Todo (loop tracker) — check off only when harness + smoke pass

- [x] T0 scaffold git-ready + SPEC + flags + mock harness + CI
  - Acceptance: pytest green, smoke mock mp4 exists
  - Verify: `python -m pytest tests/ -q` + `python scripts/smoke_e2e.py --providers mock --seconds 15`
- [x] T0b unit + integration suites split (29 tests: tests/unit + tests/integration)
- [x] T1 language/host-face generic inputs + IAvatarMaker module + B-roll docs
- [x] T2 real script provider (Ollama qwen2.5:7b via local API, VRAM unload after gen)
- [x] T3-partial real TTS: piper neural voice (offline, Windows-friendly); kokoro/xtts clone still open
- [ ] T3-full realistic host voice: kokoro-82M or XTTS clone from user voice sample
- [x] T4 real avatar provider (MuseTalk v1.5 fp16, 8GB-safe) behind flag
- [x] T4a expressive avatar: musetalk lip-sync VERIFIED (mouth-band motion avg 7.5 over 3-min video, 24fps inference)
- [ ] T4b sadtalker256 Unlocked (lip+motion+emotion, score 2, ~11 min/3-min video)
- [ ] T4b expression judging: landmark-motion-std check vs static baseline in harness
- [ ] T5 compose slice (whisper + ffmpeg) real
- [ ] T6 optional VLM gate + video-LLM B-roll (both default OFF)
- [ ] T7 daily Task Scheduler job + docs + first public commit/push
