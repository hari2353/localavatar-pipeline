# Plan: LocalAvatar-Pipeline (engineering loop)

Loop per task: SPEC -> implement slice -> harness `pytest` -> smoke -> commit.
Never load 2 GPU engines at once (8GB VRAM rule). Unload between stages.

## Phase 0 - Git-ready + harness (YOU ARE HERE)
- [x] scaffold + SPEC + flags + mocks + CI
- Verify: `pytest` green on fresh clone, `git status` shows only source files.
- Checkpoint: human reviews SPEC Open Questions, approves flag names.

## Phase 1 - Script + Voice slice
- Ollama Qwen2.5-7B-Q4 script provider; Kokoro-82M default TTS; Piper fallback; XTTS clone path behind flag.
- Verify: 450-word script -> wav, same voice id twice = same voice; LUFS check.

## Phase 2 - Avatar slice (flag: musetalk | sadtalker | latentsync)
- Default `musetalk` fp16 @720p. Others implement same `IAvatarRenderer` interface.
- Verify: 15-sec clip lip-sync sanity + <10 min on RTX 3070; interface swap needs no pipeline change.

## Phase 3 - Compose slice (subs + assembly + thumbnail)
- faster-whisper base/small -> srt -> FFmpeg burn-in + B-roll + thumb.
- Verify: mock e2e mp4 plays, srt non-empty, 30fps.

## Phase 4 - Optional intelligence (BOTH behind flags, default OFF)
- `broll_provider: wan_5b | ltx | sd15_local | none` (B-roll only, never host).
- `vlm_quality_gate: true/false` with `minicpm-v-2b | qwen2.5-vl-3b-q4` (post-render accept/retry).
- Verify: flag on/off both pass harness; VRAM sequential; time budget recorded.

## Phase 5 - Daily ops + docs
- Task Scheduler job, `outputs/` dating, README demo GIF, license table (flag XTTS CPML), viva diagrams.

Risks: 16GB RAM swap (mitigate: sequential + `--seconds` smoke first); XTTS license (mitigate: Kokoro default); LatentSync slowness (mitigate: flag, not default).
