"""Market-steal additions: burned-in subtitles + brand-aware auto thumbnail
(AutoShorts/Revid/Captions table stakes), and the auto-retry quality gate.

All offline on mocks — the post steps are flag-gated so OFF behavior is
byte-identical to today."""

from pathlib import Path

import pytest
import yaml

from src.pipeline import run
from src.post import Brand, burn_subtitles, make_thumbnail

ROOT = Path(__file__).resolve().parents[2]


def load_example():
    with open(ROOT / "configs" / "config.example.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── brand + thumbnail ────────────────────────────────────────────────────────
def test_brand_clamps_colors_and_bounds() -> None:
    brand = Brand(handle="@cha", accent="GGGGGG", title_scale=99)
    assert brand.accent == "#000000" or brand.accent.startswith("#")  # never crashes on bad hex
    assert 0.5 <= brand.title_scale <= 3.0


def test_thumbnail_is_real_bounded_image_with_brand(tmp_path: Path) -> None:
    host = tmp_path / "host.png"
    host.write_bytes(b"")  # mock maker placeholder is fine
    host.parent.mkdir(parents=True, exist_ok=True)
    # give it a real PNG body so pillow can open it
    from PIL import Image

    Image.new("RGB", (640, 360), (30, 30, 30)).save(host)
    out = make_thumbnail(
        host, "5 facts about Rust", tmp_path / "thumb.jpg",
        Brand(handle="@chatters", accent="#00ff88"),
    )
    with Image.open(out) as image:
        assert image.size == (1280, 720)  # YouTube-ready, bounded


def test_burn_subtitles_mock_fallback_keeps_timing(tmp_path: Path) -> None:
    final = tmp_path / "final.mp4"
    final.write_bytes(b"video-bytes")
    srt = tmp_path / "subs.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nhello world\n", encoding="utf-8")
    out = burn_subtitles(final, srt, tmp_path / "final_burned.mp4")
    assert out.exists() and out.read_bytes() == final.read_bytes()  # mock: copy keeps A/V


# ── pipeline wiring (flag-gated) ─────────────────────────────────────────────
def test_post_flags_off_change_nothing(tmp_path: Path) -> None:
    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    meta = run(cfg, "tech facts")
    out = tmp_path / "out"
    assert not (out / "final_burned.mp4").exists()
    assert not (out / "thumbnail.jpg").exists()
    assert "thumbnail" not in meta and "burned" not in meta
    assert meta["attempts"] == 1


def test_post_flags_on_produce_burned_and_thumbnail(tmp_path: Path) -> None:
    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["subtitles_burn"] = True
    cfg["thumbnail"] = True
    cfg["brand"] = {"handle": "@chatters", "accent": "#00ff88"}
    meta = run(cfg, "tech facts")
    out = tmp_path / "out"
    assert (out / "final_burned.mp4").exists()
    assert (out / "thumbnail.jpg").exists()
    assert meta["burned_subs"] == str(out / "final_burned.mp4")
    assert meta["thumbnail"] == str(out / "thumbnail.jpg")
    assert meta["brand"]["handle"] == "@chatters"


def test_retry_loop_varies_seed_and_reports_attempts(tmp_path: Path, monkeypatch) -> None:
    from src.providers import mock as m
    from src import factory

    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["vlm_quality_gate"] = {"enabled": True, "model": "minicpm-v-2b", "max_attempts": 3}

    seen_seeds: list[int] = []

    class FlakyGate:
        def __init__(self) -> None:
            self.calls = 0

        def review(self, clip) -> bool:
            self.calls += 1
            return self.calls >= 2  # fail once, then accept

    monkeypatch.setattr(factory, "make_quality_gate", lambda *a, **k: FlakyGate())

    class SeedSpyMaker(m.MockAvatarMaker):
        def ensure(self, out_png, seed: int = 42):
            seen_seeds.append(seed)
            return super().ensure(out_png, seed)

    monkeypatch.setattr(factory, "make_avatar_maker", lambda flag: SeedSpyMaker())
    meta = run(cfg, "tech facts")
    assert meta["attempts"] == 2
    assert meta["accepted"] is True
    assert len(seen_seeds) == 2 and seen_seeds[0] != seen_seeds[1]  # seed varied


def test_retry_exhaustion_is_honest(tmp_path: Path, monkeypatch) -> None:
    from src import factory

    cfg = load_example()
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["vlm_quality_gate"] = {"enabled": True, "model": "minicpm-v-2b", "max_attempts": 2}

    class AlwaysFail:
        def review(self, clip) -> bool:
            return False

    monkeypatch.setattr(factory, "make_quality_gate", lambda *a, **k: AlwaysFail())
    meta = run(cfg, "tech facts")
    assert meta["attempts"] == 2 and meta["accepted"] is False
