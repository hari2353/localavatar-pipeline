import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.flags import VALID, validate


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
    import pytest
    cfg = base_cfg()
    cfg["engines"]["tts_provider"] = "elevenlabs_cloud"
    with pytest.raises(ValueError):
        validate(cfg)
