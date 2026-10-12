# Todo (loop tracker) — check off only when harness + smoke pass

- [x] T0 scaffold git-ready + SPEC + flags + mock harness + CI
  - Acceptance: pytest green, smoke mock mp4 exists
  - Verify: `python -m pytest tests/ -q` + `python scripts/smoke_e2e.py --providers mock --seconds 15`
- [ ] T1 answer SPEC Open Questions (niche, language, host face, broll v1)
- [ ] T2 real script provider (Ollama) behind flag
- [ ] T3 real TTS provider (Kokoro default) behind flag
- [ ] T4 real avatar provider (MuseTalk default) behind flag
- [ ] T5 compose slice (whisper + ffmpeg) real
- [ ] T6 optional VLM gate + video-LLM B-roll (both default OFF)
- [ ] T7 daily Task Scheduler job + docs + first public commit/push
