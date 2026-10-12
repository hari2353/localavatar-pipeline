"""Unit: factory maps every flag to the right provider class (no GPU work)."""
import pytest

from src import factory
from src.providers import mock as m


def test_mock_flags_map_to_mocks():
    assert isinstance(factory.make_script_provider("mock"), m.MockScript)
    assert isinstance(factory.make_tts_provider("mock"), m.MockTTS)
    assert isinstance(factory.make_avatar_renderer("mock"), m.MockAvatar)
    assert isinstance(factory.make_avatar_maker("mock"), m.MockAvatarMaker)
    assert isinstance(factory.make_broll_provider("mock"), m.MockBroll)
    assert isinstance(factory.make_broll_provider("none"), m.NullBroll)
    assert isinstance(factory.make_quality_gate(False, "minicpm-v-2b"), m.PassThroughGate)


def test_avatar_maker_none_is_strict():
    assert isinstance(factory.make_avatar_maker("none"), m.ExistingFileAvatarMaker)


@pytest.mark.parametrize("fn,flag", [
    (factory.make_script_provider, "ollama_qwen"),
    (factory.make_tts_provider, "kokoro"),
    (factory.make_tts_provider, "xtts"),
    (factory.make_avatar_renderer, "musetalk"),
    (factory.make_avatar_maker, "sd15_local"),
    (factory.make_broll_provider, "wan_5b"),
])
def test_real_engines_reserved_for_later_tasks(fn, flag):
    with pytest.raises(NotImplementedError):
        fn(flag)


def test_no_torch_at_import():
    import sys
    assert "torch" not in sys.modules, "src must not import torch at top level"
