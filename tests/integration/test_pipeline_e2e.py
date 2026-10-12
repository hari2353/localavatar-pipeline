"""Integration: full pipeline end-to-end on mocks (CPU-only, no downloads)."""
from pathlib import Path

import yaml

from src.pipeline import run

ROOT = Path(__file__).resolve().parents[2]


def load_example():
    with open(ROOT / "configs" / "config.example.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_mock_pipeline_e2e(tmp_path):
    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    meta = run(cfg, "tech facts")
    out = tmp_path / "out"
    assert (out / "final.mp4").exists()
    assert (out / "voice.wav").exists() and (out / "avatar.mp4").exists()
    assert (out / "subs.srt").exists() and (out / "meta.json").exists()
    assert meta["accepted"] is True
    assert meta["niche"] == "tech facts"


def test_language_and_host_image_flow_to_meta(tmp_path):
    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["tts"]["language"] = "ur"
    cfg["host_image"] = str(tmp_path / "myhost.png")
    (tmp_path / "myhost.png").write_bytes(b"user-face")
    meta = run(cfg, "tech facts")
    assert meta["language"] == "ur"
    assert meta["host_image"].endswith("myhost.png")


def test_missing_host_face_is_auto_created(tmp_path):
    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["host_image"] = str(tmp_path / "faces" / "host.png")
    meta = run(cfg, "tech facts")
    assert Path(meta["host_image"]).exists()


def test_strict_avatar_maker_fails_loudly(tmp_path):
    import pytest
    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["engines"]["avatar_maker"] = "none"
    cfg["host_image"] = str(tmp_path / "nope.png")
    with pytest.raises(FileNotFoundError):
        run(cfg, "tech facts")


def test_broll_mock_variant_e2e(tmp_path):
    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["engines"]["broll_provider"] = "mock"
    meta = run(cfg, "tech facts")
    assert (tmp_path / "out" / "final.mp4").exists() and meta["accepted"] is True
