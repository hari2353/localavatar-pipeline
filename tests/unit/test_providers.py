"""Unit: each mock provider satisfies its ABC contract in isolation."""
from pathlib import Path

import pytest

from src.interfaces import (AudioTrack, IAvatarMaker, IAvatarRenderer, IBrollProvider,
                            IQualityGate, IScriptProvider, ITTSProvider, Script, VideoClip)
from src.providers import mock as m


def test_mock_script_shape():
    s = m.MockScript().generate("tech facts", minutes=3, seed=1)
    assert isinstance(s, Script) and s.title and len(s.sections) == 3 and len(s.full_text) > 100


def test_mock_tts_writes_wav(tmp_path):
    s = m.MockScript().generate("n", 1, 1)
    a = m.MockTTS().synthesize(s, tmp_path / "v.wav", "af_heart")
    assert isinstance(a, AudioTrack) and a.wav_path.exists() and a.duration_s > 0


def test_mock_avatar_writes_mp4(tmp_path):
    c = m.MockAvatar().render(Path("x.png"), AudioTrack(Path("a.wav"), 3.0), tmp_path / "a.mp4")
    assert isinstance(c, VideoClip) and c.mp4_path.exists()


def test_avatar_maker_creates_missing_face(tmp_path):
    p = m.MockAvatarMaker().ensure(tmp_path / "faces" / "host.png", seed=7)
    assert p.exists()


def test_avatar_maker_none_requires_user_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        m.ExistingFileAvatarMaker().ensure(tmp_path / "missing.png")


def test_broll_none_empty_and_mock_one_artifact(tmp_path):
    s = m.MockScript().generate("n", 1, 1)
    assert m.NullBroll().generate(s, tmp_path) == []
    assert len(m.MockBroll().generate(s, tmp_path)) == 1


def test_gate_off_always_accepts(tmp_path):
    c = VideoClip(tmp_path / "c.mp4", 3.0)
    assert m.PassThroughGate().review(c) is True


def test_all_mocks_implement_own_abc():
    assert isinstance(m.MockScript(), IScriptProvider)
    assert isinstance(m.MockTTS(), ITTSProvider)
    assert isinstance(m.MockAvatar(), IAvatarRenderer)
    assert isinstance(m.MockAvatarMaker(), IAvatarMaker)
    assert isinstance(m.ExistingFileAvatarMaker(), IAvatarMaker)
    assert isinstance(m.NullBroll(), IBrollProvider)
    assert isinstance(m.MockBroll(), IBrollProvider)
    assert isinstance(m.PassThroughGate(), IQualityGate)
