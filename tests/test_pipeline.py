import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import factory
from src.interfaces import IBrollProvider


def test_mock_pipeline_e2e(tmp_path):
    from src.pipeline import run
    import yaml
    with open(ROOT / "configs" / "config.example.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["out_dir"] = str(tmp_path / "out")
    meta = run(cfg, "tech facts")
    assert (tmp_path / "out" / "final.mp4").exists()
    assert (tmp_path / "out" / "subs.srt").exists()
    assert meta["accepted"] is True


def test_vlm_gate_off_passes_and_broll_none_ok(tmp_path):
    gate = factory.make_quality_gate(False, "minicpm-v-2b")
    from src.providers.mock import MockAvatar
    from src.interfaces import AudioTrack
    clip = MockAvatar().render(Path("x.png"), AudioTrack(Path("a.wav"), 3.0), tmp_path / "o.mp4")
    assert gate.review(clip) is True


def test_no_torch_at_import():
    assert "torch" not in sys.modules, "src must not import torch at top level"
