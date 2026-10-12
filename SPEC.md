# Spec: LocalAvatar-Pipeline (100% local, open-source, daily 3-min AI host video)

## Objective
Input `niche + minutes(=3)` -> output MP4 with fixed AI host (photo avatar + cloned voice), subtitles, B-roll, thumbnail. Runs end-to-end on a single laptop GPU (target: RTX 3070 Laptop 8GB, 16GB RAM, Windows 11). One command daily. User picks engines via feature flags, no code edits.

Success = `python scripts/smoke_e2e.py --providers mock` passes on a fresh clone with no GPU, and the same command with real flags renders a 3-min video on the target laptop in <45 min.

## Tech Stack
- Python 3.11, FFmpeg 6 (NVENC), Ollama (LLM/VLM), PyTorch cu117 (real providers only)
- Real engines (lazy, optional): Kokoro-82M / XTTS-v2 / Piper | MuseTalk / SadTalker / LatentSync | faster-whisper | GFPGAN | Wan-2.2-5B-GGUF or LTX-Video (B-roll only) | MiniCPM-V-2B or Qwen2.5-VL-3B-Q4 (quality gate)
- Harness: pytest, no torch/transformers at import time

## Commands
```powershell
# mock (works everywhere, CI + fresh clone)
python -m pytest tests/ -q
python scripts/smoke_e2e.py --providers mock --niche "tech facts" --seconds 15

# daily real run (target laptop)
copy configs\config.example.yaml config.yaml   # then edit flags
python scripts/run_daily.py --config config.yaml --niche "tech facts" --minutes 3

# lint/format
python -m compileall src tests scripts
```

## Project Structure
```
SPEC.md                  -> this file (source of truth)
tasks/plan.md            -> engineering plan + verify checkpoints
tasks/todo.md            -> task list ( Lopez loop tracker)
configs/config.example.yaml -> all feature flags (copy to config.yaml, gitignored)
src/flags.py             -> flag loading + validation + env overrides
src/interfaces.py        -> SOLID ABCs (IScriptProvider, ITTSProvider, IAvatarRenderer, IBrollProvider, IQualityGate, ICompositor)
src/factory.py           -> flag -> provider instance (DI, lazy imports)
src/pipeline.py          -> orchestrator, runs stages sequentially (VRAM-safe)
src/providers/mock.py    -> offline fakes for harness/CI
scripts/run_daily.py     -> CLI entry, real daily job
scripts/smoke_e2e.py     -> end-to-end loop check (mock or real)
tests/                   -> harness: flags + contracts + pipeline order (CPU-only)
models/ outputs/ voices/ -> gitignored, local-only
```

## Code Style
- stdlib + ABCs in `src/`; heavy deps (`torch`, `TTS`, `musetalk`) imported ONLY inside provider methods, never at module top.
- snake_case, type hints, docstrings on interfaces. Example:
```python
class ITTSProvider(abc.ABC):
    name: str
    @abc.abstractmethod
    def synthesize(self, script: Script, out_wav: Path) -> AudioTrack: ...
```

## Testing Strategy (harness engineering)
- `tests/unit/` — isolated, no pipeline: flag validation + env overrides, factory flag->class mapping (real engines assert `NotImplementedError` until their task lands), each mock vs its ABC, no-torch-at-import guard.
- `tests/integration/` — mock e2e: full `pipeline.run` artifacts + meta, language/host-image passthrough, missing-face auto-create vs strict-`none` failure, B-roll variants, CLI via subprocess (`run_daily.py` flags, `smoke_e2e.py`).
- Commands: `pytest tests/unit -q` (fast) | `pytest tests/integration -q` (loop) | `pytest tests/ -q` (gate before every commit).
- Coverage gate: harness passes on `requirements.txt` alone (no GPU wheels). Real-model checks are manual, checklist in tasks/plan.md.

## Boundaries
- Always: run `pytest` before commit; keep `SPEC.md` updated when flags change; lazy-import GPU libs; sequential stage execution.
- Ask first: adding a new engine/dependency, changing flag names, touching CI.
- Never: commit `config.yaml` with personal paths, `models/`, `outputs/`, voice references, secrets/API keys; commit code that imports torch at top level of `src/`.

## Success Criteria
1. Fresh clone + `pip install -r requirements.txt` + `pytest` green, no GPU.
2. `smoke_e2e --providers mock` produces `outputs/smoke/final.mp4` + `.srt` + `meta.json`.
3. Same CLI with `avatar_renderer: musetalk`, `tts: kokoro` renders 3-min video on RTX 3070 8GB in <45 min.
4. Flag flips (`avatar_renderer: sadtalker`, `vlm_quality_gate: true/false`, `broll: none/sd15_local`) need zero code changes.
5. `git status` clean of models/outputs/secrets; push-ready.

## Open Questions (resolved 2026-10-12)
1. ~~Niche + language~~ -> both generic user inputs (`--niche`, `--language`, config `tts.language`).
2. ~~Host face~~ -> generic user input (`--host-image` / `host_image`) + `IAvatarMaker` module (`avatar_maker: none|mock|sd15_local`).
3. ~~B-roll v1~~ -> `none` default. B-roll = cutaway visuals over the host voice (see README). Local gen (`sd15_local|wan_5b|ltx`) lands in T6.
