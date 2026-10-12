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

## Phase 2 - Avatar slice (flag: musetalk | sadtalker256 | latentsync | ffmpeg_slideshow)
- T4a `musetalk` fp16 @720p: lip-sync only (expression score 1). Realtime-class, tested on 4GB laptop GPUs. Daily default.
- T4b `sadtalker256` (SadTalker-Unlocked, 256px, no GFPGAN, still mode): lip + head motion + emotion from audio prosody (score 2). ~40s per 11s audio => ~11 min per 3-min video on 8GB. 512px+GFPGAN excluded (peaks 8.2GB+, OOM).
- Both implement `IAvatarRenderer`; swap needs no pipeline change.
- Verify: 15-sec clip lip-sync sanity + expression-variance check (facial landmark motion std > static baseline); time budget recorded.

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
