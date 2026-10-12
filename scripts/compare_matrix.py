"""Compare matrix: same niche x every provider combo -> REPORT.md with playability verdicts.

Usage: python scripts/compare_matrix.py --niche "tech facts" --minutes 1
Each combo renders into outputs/compare/<combo>/; failures are recorded, not fatal.
"""
import argparse
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import run  # noqa: E402


def ffprobe_info(mp4: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size", "-show_entries", "stream=codec_type",
                        "-of", "json", str(mp4)], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return {"playable": False, "error": "moov atom not found (placeholder bytes)"}
    try:
        j = json.loads(r.stdout)
        kinds = sorted({s["codec_type"] for s in j.get("streams", [])})
        return {"playable": kinds == ["audio", "video"],
                "duration_s": round(float(j["format"]["duration"]), 1),
                "streams": kinds}
    except Exception as e:  # noqa: BLE001
        return {"playable": False, "error": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", default="tech facts")
    ap.add_argument("--minutes", type=int, default=1)
    ap.add_argument("--out", default="outputs/compare")
    args = ap.parse_args()

    with open(ROOT / "configs" / "config.example.yaml", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    combos = list(itertools.product(
        ["template", "mock"],            # script_provider
        ["sapi", "mock"],                # tts_provider
        ["pillow_face", "mock"],         # avatar_maker
        ["ffmpeg_slideshow", "mock"],    # avatar_renderer
    ))

    results = []
    for script_p, tts_p, maker_p, rend_p in combos:
        name = f"{script_p}+{tts_p}+{maker_p}+{rend_p}"
        d = Path(args.out) / name.replace("+", "_")
        cfg = yaml.safe_load(yaml.safe_dump(base))
        cfg["out_dir"] = str(d)
        cfg["minutes"] = args.minutes
        cfg["host_image"] = str(d / "host.png")
        cfg["engines"].update({"script_provider": script_p, "tts_provider": tts_p,
                               "avatar_maker": maker_p, "avatar_renderer": rend_p})
        t0 = time.time()
        try:
            meta = run(cfg, args.niche)
            info = ffprobe_info(d / "final.mp4")
            row = {"combo": name, "ok": True, "render_s": round(time.time() - t0, 1),
                   "final_kb": round((d / "final.mp4").stat().st_size / 1024, 1), **info}
        except Exception as e:  # noqa: BLE001
            row = {"combo": name, "ok": False, "error": f"{type(e).__name__}: {str(e)[-160:]}",
                   "render_s": round(time.time() - t0, 1)}
        results.append(row)
        print(row, flush=True)

    playable = [r for r in results if r.get("playable")]
    report = ["# Compare matrix (same niche, mock vs studio tiers)", "",
              f"niche={args.niche} minutes={args.minutes}", "",
              "| combo | ok | playable | duration_s | final_kb | render_s | note |",
              "|---|---|---|---|---|---|---|"]
    for r in results:
        report.append(f"| {r['combo']} | {r.get('ok')} | {r.get('playable', False)} | "
                      f"{r.get('duration_s', '-')} | {r.get('final_kb', '-')} | {r['render_s']} | "
                      f"{r.get('error', '')} |")
    report += ["", f"PLAYABLE: {len(playable)}/{len(results)}",
               "Expression score (audio->face, judged separately, all current combos = 0):",
               "  0 = static card (ffmpeg_slideshow), no audio link",
               "  1 = lip-sync only (musetalk, T4a) — mouth follows audio, flat emotion",
               "  2 = lip + head motion + emotion (sadtalker256, T4b) — expressions follow audio prosody",
               "Upgrade path: T4a musetalk fp16 (realtime on 4GB+ VRAM, fast daily) then "
               "T4b sadtalker256 no-GFPGAN via SadTalker-Unlocked (chunked, fits 8GB; "
               "~40s per 11s audio => ~11 min for 3 min). 512px+GFPGAN peaks 8.2GB+ = OOM on 8GB cards, excluded."]
    (Path(args.out) / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    (Path(args.out) / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"WROTE {args.out}/REPORT.md  playable={len(playable)}/{len(results)}")


if __name__ == "__main__":
    main()
