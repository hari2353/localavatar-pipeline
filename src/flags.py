"""Feature-flag loading + validation. YAML + env overrides (LAP_*)."""
import os
from pathlib import Path

import yaml

VALID = {
    "script_provider": {"mock", "template", "ollama_qwen", "ollama_llama"},
    "tts_provider": {"mock", "sapi", "kokoro", "xtts", "piper"},
    "avatar_renderer": {"mock", "ffmpeg_slideshow", "musetalk", "sadtalker", "latentsync"},
    "avatar_maker": {"none", "mock", "pillow_face", "sd15_face", "sd15_local"},
    "broll_provider": {"none", "mock", "sd15_local", "wan_5b", "ltx"},
    "enhancer": {"none", "gfpgan"},
    "vlm_model": {"minicpm-v-2b", "qwen2.5-vl-3b-q4"},
}

ENV_MAP = {
    "LAP_SCRIPT": ("engines", "script_provider"),
    "LAP_TTS": ("engines", "tts_provider"),
    "LAP_AVATAR": ("engines", "avatar_renderer"),
    "LAP_BROLL": ("engines", "broll_provider"),
    "LAP_VLM_GATE": ("vlm_quality_gate", "enabled"),
}


def load_config(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for env, (section, key) in ENV_MAP.items():
        if env in os.environ:
            val = os.environ[env]
            if key == "enabled":
                val = val.lower() in {"1", "true", "yes"}
            cfg[section][key] = val
    validate(cfg)
    return cfg


def validate(cfg: dict) -> None:
    eng = cfg["engines"]
    for key in ("script_provider", "tts_provider", "avatar_renderer", "avatar_maker", "broll_provider", "enhancer"):
        if eng[key] not in VALID[key]:
            raise ValueError(f"invalid {key}={eng[key]!r}, allowed={sorted(VALID[key])}")
    if cfg["vlm_quality_gate"]["model"] not in VALID["vlm_model"]:
        raise ValueError("invalid vlm model")
