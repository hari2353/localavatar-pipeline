"""Integration: CLI entry points work as a user would call them (subprocess)."""
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def run_cli(*args, cwd=ROOT):
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, timeout=120)


def test_run_daily_mock_config(tmp_path):
    with open(ROOT / "configs" / "config.example.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["out_dir"] = str(tmp_path / "out")
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    r = run_cli("scripts/run_daily.py", "--config", str(cfg_path),
                "--niche", "tech facts", "--language", "hi",
                "--host-image", str(tmp_path / "host.png"))
    assert r.returncode == 0, r.stderr
    meta = json.loads((tmp_path / "out" / "meta.json").read_text())
    assert meta["language"] == "hi" and (tmp_path / "out" / "final.mp4").exists()


def test_smoke_script_ok():
    r = run_cli("scripts/smoke_e2e.py", "--providers", "mock", "--seconds", "15")
    assert r.returncode == 0, r.stderr
    assert "SMOKE OK" in r.stdout
