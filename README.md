# LocalAvatar-Pipeline — niche in, 3-min host video out. 100% local.

## Quickstart (works on any machine, no GPU)
```powershell
cd F:\localavatar-pipeline
python -m pip install -r requirements.txt
python -m pytest tests/ -q
python scripts/smoke_e2e.py --providers mock --niche "tech facts" --seconds 15
```

## Daily real run (RTX 3070 laptop)
```powershell
copy configs\config.example.yaml config.yaml
# edit config.yaml flags (see below), place host.png + speaker.wav
python scripts/run_daily.py --config config.yaml --niche "tech facts" --minutes 3
```

## Feature flags (user decides, no code change)
All in `config.yaml` (gitignored). Example in `configs/config.example.yaml`:

| Flag | Choices | Default | Notes |
|---|---|---|---|
| `script_provider` | `mock \| ollama_qwen | ollama_llama` | `mock` | LLM writes script |
| `tts_provider` | `mock \| kokoro \| xtts \| piper` | `mock` | `kokoro`=Apache-2.0 default real; `xtts`=best clone but CPML license |
| `avatar_renderer` | `mock \| musetalk \| sadtalker \| latentsync` | `mock` | `musetalk`=recommended 8GB |
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
