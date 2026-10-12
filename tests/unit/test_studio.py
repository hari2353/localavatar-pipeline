"""Unit: studio tier providers (real local media, kept FAST for the harness)."""
from src import factory
from src.interfaces import ICompositor
from src.providers import studio as s


def test_template_script_word_budget():
    sc = s.TemplateScriptProvider().generate("tech facts", minutes=1, seed=1)
    assert 120 <= len(sc.full_text.split()) <= 220
    assert sc.sections == ["hook", "body", "cta"]


def test_sapi_speaks_short_line(tmp_path):
    from src.interfaces import Script
    sc = Script(title="t", sections=["body"], full_text="Hello. This is a voice test.")
    a = s.SapiTTSProvider().synthesize(sc, tmp_path / "v.wav")
    assert a.wav_path.exists() and a.duration_s > 1.0


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
    from src.providers import mock as m
    assert isinstance(factory.make_compositor(eng_mock), m.MockCompositor)
    assert isinstance(factory.make_compositor(eng_studio), s.CopyCompositor)
    assert isinstance(s.CopyCompositor(), ICompositor)
