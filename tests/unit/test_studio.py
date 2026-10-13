"""Unit: studio tier providers (real local media, kept FAST for the harness)."""
from pathlib import Path

from src import factory
from src.interfaces import ICompositor
from src.providers import studio as s


def test_template_script_word_budget():
    sc = s.TemplateScriptProvider().generate("tech facts", minutes=1, seed=1)
    assert 90 <= len(sc.full_text.split()) <= 150
    assert sc.sections == ["hook", "body", "cta"]
    sc3 = s.TemplateScriptProvider().generate("tech facts", minutes=3, seed=1)
    assert 300 <= len(sc3.full_text.split()) <= 400  # ~3 min at measured SAPI pace


def test_sapi_speaks_short_line(tmp_path):
    from src.interfaces import Script
    sc = Script(title="t", sections=["body"], full_text="Hello. This is a voice test.")
    a = s.SapiTTSProvider().synthesize(sc, tmp_path / "v.wav")
    assert a.wav_path.exists() and a.duration_s > 1.0


def test_piper_speaks_short_line(tmp_path):
    import pytest
    repo_root = Path(__file__).resolve().parents[2]
    if not (repo_root / "voices" / "piper" / "en_US-lessac-medium.onnx").exists():
        pytest.skip("piper voice model absent (local-only)")
    from src.interfaces import Script
    sc = Script(title="t", sections=["body"], full_text="Hello. This is the piper voice test.")
    a = s.PiperTTSProvider().synthesize(sc, tmp_path / "p.wav")
    assert a.wav_path.exists() and a.duration_s > 1.0


def test_piper_wired_in_factory():
    assert isinstance(factory.make_tts_provider("piper"), s.PiperTTSProvider)


def test_pillow_face_png(tmp_path):
    from PIL import Image
    p = s.PillowFaceMaker().ensure(tmp_path / "host.png", seed=3)
    assert Image.open(p).size == (1280, 720)


def test_slideshow_renders_real_mp4(tmp_path):
    from src.interfaces import AudioTrack, Script
    sc = Script(title="t", sections=["body"], full_text="Hello world.")
    face = s.PillowFaceMaker().ensure(tmp_path / "host.png")
    audio = s.SapiTTSProvider().synthesize(sc, tmp_path / "v.wav")
    clip = s.FfmpegSlideshowRenderer().render(face, audio, tmp_path / "a.mp4")
    assert clip.mp4_path.stat().st_size > 20_000
    assert abs(clip.duration_s - audio.duration_s) < 0.5


def test_srt_writer_splits_duration(tmp_path):
    from src.interfaces import Script
    sc = Script(title="t", sections=["body"], full_text=" ".join(["word"] * 90))
    p = s.write_srt(sc, 90.0, tmp_path / "s.srt")
    txt = p.read_text(encoding="utf-8")
    assert "00:01:30" in txt and txt.count("-->") == 10


def test_compositor_auto_select():
    eng_mock = {"script_provider": "mock", "tts_provider": "mock",
                "avatar_renderer": "mock", "avatar_maker": "mock",
                "broll_provider": "none", "enhancer": "none"}
    eng_studio = dict(eng_mock, tts_provider="sapi")
    eng_new = {"script_provider": "ollama_qwen", "tts_provider": "piper",
               "avatar_renderer": "musetalk", "avatar_maker": "none",
               "broll_provider": "none", "enhancer": "none"}
    from src.providers import mock as m
    assert isinstance(factory.make_compositor(eng_mock), m.MockCompositor)
    assert isinstance(factory.make_compositor(eng_studio), s.CopyCompositor)
    # regression: every real engine flag must yield real output, never mock bytes
    assert isinstance(factory.make_compositor(eng_new), s.CopyCompositor)
    assert isinstance(s.CopyCompositor(), ICompositor)


def test_ollama_prompt_shape():
    p = s.build_script_prompt("tech facts", 115, 7)
    assert "tech facts" in p and "115" in p and "markdown" in p


def test_ollama_wired_in_factory():
    assert isinstance(factory.make_script_provider("ollama_qwen"),
                      s.OllamaScriptProvider)


def test_vllm_payload_shape_and_wiring():
    p = s.build_chat_payload("Qwen2.5-7B-Instruct-AWQ", "tech facts", 115, 7)
    assert p["model"] == "Qwen2.5-7B-Instruct-AWQ"
    assert "tech facts" in p["messages"][0]["content"] and p["max_tokens"] == 230
    assert isinstance(factory.make_script_provider("vllm"), s.VLLMScriptProvider)
