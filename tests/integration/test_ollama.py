"""Integration: live Ollama script generation (needs `ollama serve`, ~1 min)."""
import pytest

from src.providers.studio import OLLAMA_MODELS, OllamaScriptProvider


def test_ollama_writes_short_script():
    import json
    import urllib.request

    try:
        payload = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5).read()
    except Exception:  # noqa: BLE001
        pytest.skip("ollama serve not running")
    ollama_qwen = OLLAMA_MODELS["ollama_qwen"]
    pulled = [m["name"] for m in json.loads(payload).get("models", [])]
    if not any(name == ollama_qwen or name.startswith(ollama_qwen + ":") for name in pulled):
        pytest.skip(f"ollama model {ollama_qwen} not pulled")
    sc = OllamaScriptProvider("ollama_qwen").generate("tech facts", minutes=1, seed=3, word_budget=40)
    assert sc.title == "tech facts daily brief"
    assert 15 <= len(sc.full_text.split()) <= 120
