"""Orchestrator: sequential stages (VRAM-safe). One GPU engine resident at a time."""
from pathlib import Path

from . import factory


def run(cfg: dict, niche: str) -> dict:
    out = Path(cfg.get("out_dir", "outputs"))
    out.mkdir(parents=True, exist_ok=True)
    minutes = int(cfg.get("minutes", 3))
    seed = int(cfg.get("seed", 42))
    eng = cfg["engines"]

    script = factory.make_script_provider(eng["script_provider"]).generate(niche, minutes, seed)
    audio = factory.make_tts_provider(eng["tts_provider"]).synthesize(
        script, out / "voice.wav", cfg.get("tts", {}).get("voice_id", ""))
    clip = factory.make_avatar_renderer(eng["avatar_renderer"]).render(
        Path(cfg.get("host_image", "assets/host.png")), audio, out / "avatar.mp4")
    broll = factory.make_broll_provider(eng["broll_provider"]).generate(script, out)
    gate = factory.make_quality_gate(cfg["vlm_quality_gate"]["enabled"], cfg["vlm_quality_gate"]["model"])
    accepted = gate.review(clip)
    final = out / "final.mp4"
    final.write_bytes(b"mock-mp4")
    (out / "subs.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\n" + script.title + "\n")
    meta = {"niche": niche, "minutes": minutes, "engines": eng,
            "vlm_gate": cfg["vlm_quality_gate"], "accepted": accepted,
            "artifacts": [str(final), str(out / "subs.srt")]}
    import json
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta
