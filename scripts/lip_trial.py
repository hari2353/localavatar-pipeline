"""Lip-sync trial: still host face + short wav -> MuseTalk mp4. Prints fps for T4a budgeting.

Usage: python scripts/lip_trial.py --image assets/host.png --audio outputs/liptrial/line.wav --out outputs/liptrial/lip.mp4
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.interfaces import AudioTrack
from src.providers.expressive import MuseTalkRenderer


def wav_duration(wav: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(wav)], capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    dur = wav_duration(Path(args.audio))
    print(f"audio {dur:.1f}s -> rendering...", flush=True)
    t0 = time.time()
    clip = MuseTalkRenderer().render(Path(args.image), AudioTrack(Path(args.audio), dur), Path(args.out))
    el = time.time() - t0
    print(f"LIP OK -> {clip.mp4_path} ({clip.mp4_path.stat().st_size // 1024} KB) "
          f"in {el:.0f}s = {clip.duration_s * 25 / el:.1f} fps", flush=True)


if __name__ == "__main__":
    main()
