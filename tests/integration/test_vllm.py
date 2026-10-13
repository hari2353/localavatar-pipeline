"""Integration: vLLM script backend (skipped unless a compatible server is up).

Capable-machine path: `vllm serve <model>` on Linux, then
LAP_VLLM_URL=http://host:8000/v1/chat/completions pytest tests/integration/test_vllm.py
"""
import os

import pytest

from src.providers.studio import VLLMScriptProvider


def _server_up():
    import urllib.request
    url = os.environ.get("LAP_VLLM_URL", "http://localhost:8000/v1/chat/completions")
    base = url.rsplit("/v1/", 1)[0] + "/v1/models"
    try:
        urllib.request.urlopen(base, timeout=5)
        return True
    except Exception:  # noqa: BLE001
        return False


def test_vllm_writes_short_script():
    if not _server_up():
        pytest.skip("no OpenAI-compatible server (vllm serve) reachable")
    sc = VLLMScriptProvider().generate("tech facts", minutes=1, seed=3, word_budget=40)
    assert sc.title == "tech facts daily brief"
    assert 15 <= len(sc.full_text.split()) <= 120
