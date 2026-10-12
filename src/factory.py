"""Factory: flag -> provider instance. Real engines lazy-import here (T2-T6 fill them)."""
from .interfaces import IBrollProvider


def make_script_provider(flag: str):
    from .providers import mock as m, studio as s
    if flag == "template":
        return s.TemplateScriptProvider()
    if flag in ("ollama_qwen", "ollama_llama"):
        return s.OllamaScriptProvider(flag)
    if flag != "mock":
        raise NotImplementedError(f"script engine {flag!r} unknown")
    return m.MockScript()


def make_tts_provider(flag: str):
    from .providers import mock as m, studio as s
    if flag == "sapi":
        return s.SapiTTSProvider()
    if flag == "piper":
        return s.PiperTTSProvider()
    if flag != "mock":
        raise NotImplementedError(f"tts engine {flag!r} lands in T3")
    return m.MockTTS()


def make_avatar_renderer(flag: str, opts: dict | None = None):
    from .providers import mock as m, studio as s
    if flag == "ffmpeg_slideshow":
        return s.FfmpegSlideshowRenderer()
    if flag == "musetalk":
        from .providers import expressive as e
        o = opts or {}
        return e.MuseTalkRenderer(extra_margin=int(o.get("extra_margin", 10)),
                                  parsing_mode=str(o.get("parsing_mode", "jaw")),
                                  batch_size=int(o.get("batch_size", 4)),
                                  bbox_shift=int(o.get("bbox_shift", 0)))
    if flag in ("sadtalker", "latentsync"):
        raise NotImplementedError(f"avatar engine {flag!r} lands in T4b (SPEC offset)")
    if flag != "mock":
        raise NotImplementedError(f"avatar engine {flag!r} unknown")
    return m.MockAvatar()


def make_avatar_maker(flag: str):
    from .providers import mock as m, studio as s
    if flag == "none":
        return m.ExistingFileAvatarMaker()
    if flag == "pillow_face":
        return s.PillowFaceMaker()
    if flag == "sd15_face":
        return s.SD15FaceMaker()
    if flag != "mock":
        raise NotImplementedError(f"avatar-maker engine {flag!r} lands in T6")
    return m.MockAvatarMaker()


def make_broll_provider(flag: str):
    from .providers import mock as m
    if flag == "none":
        return m.NullBroll()
    if flag != "mock":
        raise NotImplementedError(f"broll engine {flag!r} lands in T6")
    return m.MockBroll()


def make_quality_gate(enabled: bool, model: str):
    from .providers import mock as m
    if not enabled:
        return m.PassThroughGate()
    if model not in ("minicpm-v-2b", "qwen2.5-vl-3b-q4"):
        raise ValueError(model)
    raise NotImplementedError(f"vlm gate {model!r} lands in T6")


def make_compositor(eng: dict):
    """Real copy whenever ANY engine is real; mock bytes only for all-mock runs.

    (Never allowlist real flags — a new engine must fail loud toward real output,
    not silently toward placeholder bytes.)
    """
    from .providers import mock as m, studio as s
    if all(v in ("mock", "none") for v in eng.values()):
        return m.MockCompositor()
    return s.CopyCompositor()
