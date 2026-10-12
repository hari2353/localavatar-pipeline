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


def make_avatar_renderer(flag: str):
    from .providers import mock as m, studio as s
    if flag == "ffmpeg_slideshow":
        return s.FfmpegSlideshowRenderer()
    if flag == "musetalk":
        from .providers import expressive as e
        return e.MuseTalkRenderer()
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
    """Studio tier (any template/sapi/pillow_face/ffmpeg_slideshow flag) -> real copy; else mock bytes."""
    from .providers import mock as m, studio as s
    if set(eng.values()) & s.STUDIO_ENGINES:
        return s.CopyCompositor()
    return m.MockCompositor()
