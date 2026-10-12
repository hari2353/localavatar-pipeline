"""Unit: flag loading + validation in isolation (no pipeline)."""
import copy
from pathlib import Path

import pytest
import yaml

from src.flags import VALID, load_config, validate

ROOT = Path(__file__).resolve().parents[2]


def base_cfg():
    with open(ROOT / "configs" / "config.example.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_example_config_validates():
    validate(base_cfg())


def test_all_flag_combos_validate():
    cfg = base_cfg()
    for key, allowed in VALID.items():
        if key == "vlm_model":
            continue
        for val in allowed:
            c = copy.deepcopy(cfg)
            c["engines"][key] = val
            validate(c)


def test_unknown_engine_rejected():
    cfg = base_cfg()
    cfg["engines"]["tts_provider"] = "elevenlabs_cloud"
    with pytest.raises(ValueError):
        validate(cfg)


def test_env_override_applies(tmp_path, monkeypatch):
    cfg_path = tmp_path / "c.yaml"
    cfg_path.write_text(yaml.safe_dump(base_cfg()), encoding="utf-8")
    monkeypatch.setenv("LAP_BROLL", "mock")
    monkeypatch.setenv("LAP_VLM_GATE", "true")
    cfg = load_config(cfg_path)
    assert cfg["engines"]["broll_provider"] == "mock"
    assert cfg["vlm_quality_gate"]["enabled"] is True


def test_env_override_invalid_rejected(tmp_path, monkeypatch):
    cfg_path = tmp_path / "c.yaml"
    cfg_path.write_text(yaml.safe_dump(base_cfg()), encoding="utf-8")
    monkeypatch.setenv("LAP_TTS", "not_a_engine")
    with pytest.raises(ValueError):
        load_config(cfg_path)
