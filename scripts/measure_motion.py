"""Motion judge: measures lip-sync motion in an mp4 (the T4 expression gate, mechanized).

Usage: python scripts/measure_motion.py --video outputs/x/final.mp4 [--fps 2]
Verdict: MOTION OK if mouth-band mean diff avg > 5 and localized (full-frame avg < 4).
"""
import argparse
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--fps", type=float, default=2.0)
    args = ap.parse_args()
    from PIL import Image
    import numpy as np

    with tempfile.TemporaryDirectory() as td:
        pat = str(Path(td) / "m%03d.png")
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", args.video,
                            "-vf", f"fps={args.fps}", pat],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print("MOTION FAIL: ffmpeg extract failed");
            sys.exit(2)
        fs = sorted(Path(td).glob("m*.png"))
        if len(fs) < 3:
            print("MOTION FAIL: too few frames");
            sys.exit(2)
        ref = np.asarray(Image.open(fs[0]).convert("L"), dtype=float)
        h, w = ref.shape
        my0, my1, mx0, mx1 = int(h * 0.55), int(h * 0.75), int(w * 0.3), int(w * 0.7)
        full, mouth = [], []
        for f in fs[1:]:
            d = np.abs(ref - np.asarray(Image.open(f).convert("L"), dtype=float))
            full.append(float(d.mean()))
            mouth.append(float(d[my0:my1, mx0:mx1].mean()))
        favg, mavg = statistics.mean(full), statistics.mean(mouth)
        wide = sum(1 for m in mouth if m > 8)
        print(f"frames={len(fs)} full-avg={favg:.2f} mouth-avg={mavg:.2f} wide-open={wide}/{len(mouth)}")
        if mavg > 5.0 and favg < 4.0:
            print("MOTION OK: localized lip motion present")
        else:
            print("MOTION FAIL: static or global motion (not lip-sync)")
            sys.exit(1)


if __name__ == "__main__":
    main()
