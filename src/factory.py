"""Factory: flag -> provider instance. Real engines lazy-import here (T2-T6 fill them)."""
from .interfaces import IBrollProvider


def make_script_provider(flag: str):
    from .providers import mock as m
    if flag in ("mock", "ollama_qwen", "ollama_llama") and flag != "mock":
        raise NotImplementedError(f"script engine {flag!r} lands in T2 (SPEC offset)")
    return m.MockScript() if flag == "mock" else m.MockScript()


def make_tts_provider(flag: str):
    from .providers import mock as m
    if flag != "mock":
        raise NotImplementedError(f"tts engine {flag!r} lands in T3")
    return m.MockTTS()


def make_avatar_renderer(flag: str):
    from .providers import mock as m
    if flag != "mock":
        raise NotImplementedError(f"avatar engine {flag!r} lands in T4")
    return m.MockAvatar()


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
