# Todo (loop tracker) — check off only when harness + smoke pass

- [x] T0 scaffold git-ready + SPEC + flags + mock harness + CI
  - Acceptance: pytest green, smoke mock mp4 exists
  - Verify: `python -m pytest tests/ -q` + `python scripts/smoke_e2e.py --providers mock --seconds 15`
- [x] T0b unit + integration suites split (29 tests: tests/unit + tests/integration)
- [x] T1 language/host-face generic inputs + IAvatarMaker module + B-roll docs
- [ ] T2 real script provider (Ollama) behind flag
- [ ] T3 real TTS provider (Kokoro default) behind flag
- [ ] T4 real avatar provider (MuseTalk default) behind flag
- [ ] T4a expressive avatar: musetalk (lip-sync, score 1) then sadtalker256 Unlocked (lip+motion+emotion, score 2, ~11 min/3-min video); 512px+GFPGAN excluded (OOM on 8GB)
- [ ] T4b expression judging: landmark-motion-std check vs static baseline in harness
- [ ] T5 compose slice (whisper + ffmpeg) real
- [ ] T6 optional VLM gate + video-LLM B-roll (both default OFF)
- [ ] T7 daily Task Scheduler job + docs + first public commit/push
