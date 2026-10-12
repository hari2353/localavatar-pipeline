"""Engineering-loop smoke: full run with mocks (or chosen flags), no downloads."""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--providers", default="mock", help="mock = all-mock e2e")
    ap.add_argument("--niche", default="tech facts")
    ap.add_argument("--seconds", type=int, default=15)
    ap.add_argument("--out", default="outputs/smoke")
    args = ap.parse_args()
    with open(ROOT / "configs" / "config.example.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.providers == "mock":
        cfg["engines"] = {k: ("none" if k == "broll_provider" else "mock") for k in cfg["engines"]}
        cfg["vlm_quality_gate"]["enabled"] = False
    tmp = Path(tempfile.mkdtemp())
    cfg["out_dir"] = args.out
    meta = run(cfg, args.niche)
    assert Path(cfg["out_dir"], "final.mp4").exists(), "smoke failed: no mp4"
    print(f"SMOKE OK ({args.niche}) -> {cfg['out_dir']}/final.mp4")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
