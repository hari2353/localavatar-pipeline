# LocalAvatar-Pipeline — niche in, 3-min host video out. 100% local.

## Quickstart (works on any machine, no GPU)
```powershell
cd F:\localavatar-pipeline
python -m pip install -r requirements.txt
python -m pytest tests/unit -q          # fast unit slice
python -m pytest tests/integration -q   # end-to-end loop on mocks
python scripts/smoke_e2e.py --providers mock --niche "tech facts" --seconds 15
```

## Daily real run (RTX 3070 laptop)
```powershell
copy configs\config.example.yaml config.yaml
# edit config.yaml flags (see below). Studio tier = real playable video, zero downloads:
# script_provider: template | tts_provider: sapi | avatar_maker: pillow_face | avatar_renderer: ffmpeg_slideshow
python scripts/run_daily.py --config config.yaml --niche "tech facts" --minutes 3 --language en
```

## B-roll (what it is)
- **A-roll** = main shot: your avatar host talking. Always present.
- **B-roll** = cutaway visuals laid OVER the host voice: stock clips, generated images, charts, maps, screen recordings. Keeps retention, hides cuts.
- Example 3-min timeline: `0:00-0:08` hook (avatar full-screen) -> `0:08-2:40` avatar shrinks to corner, B-roll full-screen per section -> `2:40-3:00` CTA (avatar full-screen) + thumbnail.
- Flags: `none` (avatar only, fastest, default) | `sd15_local|wan_5b|ltx` (local gen, slow, T6). API-stock (Pexels) excluded: needs key, not offline.

## Feature flags (user decides, no code change)
All in `config.yaml` (gitignored). Example in `configs/config.example.yaml`:

| Flag | Choices | Default | Notes |
|---|---|---|---|
| `script_provider` | `mock \| template \| ollama_qwen \| ollama_llama` | `mock` | `template`=real script, no download |
| `tts_provider` | `mock \| sapi \| kokoro \| xtts \| piper` | `mock` | `sapi`=real offline Windows voice (en) |
| `avatar_renderer` | `mock \| ffmpeg_slideshow \| musetalk \| sadtalker \| latentsync` | `mock` | `ffmpeg_slideshow`=real MP4, no GPU |
| `avatar_maker` | `none \| mock \| pillow_face \| sd15_local` | `mock` | `pillow_face`=real PNG host card |
| `broll_provider` | `none \| mock \| sd15_local \| wan_5b \| ltx` | `none` | video-LLM is B-roll only, default OFF |
| `vlm_quality_gate` | `false \| true` + `vlm_model: minicpm-v-2b \| qwen2.5-vl-3b-q4` | `false` | post-render accept/retry |
| `enhancer` | `none \| gfpgan` | `none` | optional |

Env override: `LAP_TTS=kokoro LAP_AVATAR=musetalk LAP_VLM_GATE=true`.

## SOLID map
`src/interfaces.py` = ABCs; `src/factory.py` = DI from flags; `src/pipeline.py` = orchestrator. New engine = new file implementing the ABC + 1 factory line. No pipeline edits.

## Push to GitHub
```powershell
cd F:\localavatar-pipeline
git init -b main 2>$null; git add -A; git commit -m "chore: git-ready scaffold with flags + mock harness"
gh repo create localavatar-pipeline --private --source=. --push
# no gh? -> create empty repo on github.com, then:
# git remote add origin https://github.com/<you>/localavatar-pipeline.git; git push -u origin main
```
Never committed: `config.yaml`, `models/`, `outputs/`, `voices/`, `*.wav/*.mp4` (see `.gitignore`).
