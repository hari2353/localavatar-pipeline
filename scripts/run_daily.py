"""CLI: daily job. `python scripts/run_daily.py --config config.yaml --niche X --minutes 3`"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.flags import load_config
from src.pipeline import run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--niche", default="tech facts")
    ap.add_argument("--minutes", type=int, default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.minutes:
        cfg["minutes"] = args.minutes
    meta = run(cfg, args.niche)
    print(f"OK niche={meta['niche']} engines={meta['engines']} gate={meta['vlm_gate']} -> {meta['artifacts'][0]}")


if __name__ == "__main__":
    main()
