"""Orchestrator: sequential stages (VRAM-safe). One GPU engine resident at a time.

Post-production (burned subs, auto thumbnail) is flag-gated; the quality
gate may request full re-produces (seed+1 each attempt) up to
``vlm_quality_gate.max_attempts`` — auto-retry like the hosted tools, but
the exhaustion is recorded honestly (``accepted: false``), never faked."""
from pathlib import Path

from . import factory


def _produce(cfg: dict, niche: str, seed: int, out: Path):
    """One full produce: script → voice → face → render. Returns the parts."""
    minutes = int(cfg.get("minutes", 3))
    eng = cfg["engines"]
    script = factory.make_script_provider(eng["script_provider"]).generate(niche, minutes, seed)
    language = cfg.get("tts", {}).get("language", "en")
    audio = factory.make_tts_provider(eng["tts_provider"]).synthesize(
        script, out / "voice.wav", cfg.get("tts", {}).get("voice_id", ""))
    host_path = factory.make_avatar_maker(eng["avatar_maker"]).ensure(
        Path(cfg.get("host_image", "assets/host.png")), seed)
    clip = factory.make_avatar_renderer(eng["avatar_renderer"], cfg.get("avatar", {})).render(
        host_path, audio, out / "avatar.mp4")
    return script, audio, host_path, clip, language


def run(cfg: dict, niche: str) -> dict:
    out = Path(cfg.get("out_dir", "outputs"))
    out.mkdir(parents=True, exist_ok=True)
    minutes = int(cfg.get("minutes", 3))
    seed = int(cfg.get("seed", 42))
    eng = cfg["engines"]

    gate_cfg = cfg["vlm_quality_gate"]
    max_attempts = max(1, int(gate_cfg.get("max_attempts", 1)))
    gate = factory.make_quality_gate(gate_cfg["enabled"], gate_cfg["model"])

    broll = None
    accepted = False
    attempts = 0
    current_seed = seed
    for attempts in range(1, max_attempts + 1):
        script, audio, host_path, clip, language = _produce(cfg, niche, current_seed, out)
        broll = factory.make_broll_provider(eng["broll_provider"]).generate(script, out)
        accepted = gate.review(clip)
        if accepted or attempts == max_attempts:
            break
        current_seed += 1  # retry: vary the seed so attempt 2 is a new take

    final = factory.make_compositor(eng).compose(clip, audio, broll, out / "final.mp4")
    from .providers.studio import write_srt
    write_srt(script, audio.duration_s, out / "subs.srt")

    meta = {"niche": niche, "minutes": minutes, "language": language,
            "host_image": str(host_path), "engines": eng,
            "vlm_gate": gate_cfg, "accepted": accepted, "attempts": attempts,
            "seed": current_seed,
            "artifacts": [str(final.mp4_path), str(out / "subs.srt")]}

    # post-production: flag-gated, brand-aware (AutoShorts/HeyGen steals)
    post_flags = cfg.get("post", {})
    from .post import brand_from, burn_subtitles, make_thumbnail

    brand = brand_from(cfg.get("brand"))
    meta["brand"] = {"handle": brand.handle, "accent": brand.accent}
    if cfg.get("subtitles_burn"):
        burned = burn_subtitles(final.mp4_path, out / "subs.srt", out / "final_burned.mp4")
        meta["burned_subs"] = str(burned)
        meta["artifacts"].append(str(burned))
    if cfg.get("thumbnail"):
        thumb = make_thumbnail(host_path, script.title, out / "thumbnail.jpg", brand)
        meta["thumbnail"] = str(thumb)
        meta["artifacts"].append(str(thumb))

    import json
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta
