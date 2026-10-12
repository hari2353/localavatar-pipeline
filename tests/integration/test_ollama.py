"""Integration: live Ollama script generation (needs `ollama serve`, ~1 min)."""
import pytest

from src.providers.studio import OllamaScriptProvider


def test_ollama_writes_short_script():
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:11434/", timeout=5)
    except Exception:  # noqa: BLE001
        pytest.skip("ollama serve not running")
    sc = OllamaScriptProvider("ollama_qwen").generate("tech facts", minutes=1, seed=3, word_budget=40)
    assert sc.title == "tech facts daily brief"
    assert 15 <= len(sc.full_text.split()) <= 120
