"""Expressive tier: audio-driven faces (lip-sync / emotion). Heavy deps live in
envs/musetalk + models/musetalk (both gitignored); this module only shells out,
so the test harness never imports torch."""
import os
import subprocess
from pathlib import Path

from ..interfaces import AudioTrack, IAvatarRenderer, VideoClip

ROOT = Path(__file__).resolve().parents[2]
MT = ROOT / "models" / "musetalk"
VENDOR = ROOT / "src" / "vendor"
MT_ENV_PY = ROOT / "envs" / "musetalk" / "Scripts" / "python.exe"
MT_UNET = MT / "models" / "musetalkV15" / "unet.pth"
MT_UNET_CFG = MT / "models" / "musetalkV15" / "musetalk.json"


class MuseTalkRenderer(IAvatarRenderer):
    """v1.5 lip-sync (expression score 1). 8GB-safe: fp16 + batch 4."""
    name = "musetalk"

    def _check(self):
        missing = [p for p in (MT_ENV_PY, MT_UNET, MT_UNET_CFG) if not p.exists()]
        if missing:
            raise RuntimeError(
                "MuseTalk not ready, missing: "
                + ", ".join(str(p) for p in missing)
                + " (build envs/musetalk, download weights per tasks/plan.md T4a)")

    def render(self, image: Path, audio: AudioTrack, out_mp4: Path) -> VideoClip:
        self._check()
        out_mp4 = Path(out_mp4).resolve()
        image = Path(image).resolve()
        wav = Path(audio.wav_path).resolve()
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        work = out_mp4.parent / "musetalk_work"
        work.mkdir(parents=True, exist_ok=True)
        dur = max(2.0, audio.duration_s)
        still = work / "still.mp4"
        r = subprocess.run(["ffmpeg", "-y", "-loop", "1", "-framerate", "25",
                            "-i", str(image), "-t", f"{dur:.1f}",
                            "-c:v", "libx264", "-preset", "ultrafast",
                            "-pix_fmt", "yuv420p", str(still)],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError(f"still-video build failed: {r.stderr[-400:]}")
        cfg = work / "task.yaml"
        cfg.write_text(f"task_0:\n  video_path: \"{still.as_posix()}\"\n"
                       f"  audio_path: \"{wav.as_posix()}\"\n", encoding="utf-8")
        res = work / "results"
        cmd = [str(MT_ENV_PY), "-m", "scripts.inference",
               "--inference_config", str(cfg), "--result_dir", str(res),
               "--unet_model_path", str(MT_UNET), "--unet_config", str(MT_UNET_CFG),
               "--version", "v15", "--use_float16", "--batch_size", "4",
               "--fps", "25", "--output_vid_name", "lip.mp4"]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(VENDOR) + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run(cmd, cwd=str(MT), capture_output=True, text=True, timeout=3600, env=env,
                           encoding="utf-8", errors="replace")
        cand = res / "lip.mp4"
        if r.returncode != 0 or not cand.exists():
            found = sorted(res.rglob("*.mp4"))
            if not found:
                raise RuntimeError(f"MuseTalk inference failed: {r.stderr[-800:]}")
            cand = found[0]
        # ensure narration audio present
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                                "-show_entries", "stream=codec_name", "-of", "csv=p=0",
                                str(cand)], capture_output=True, text=True)
        if not probe.stdout.strip():
            muxed = work / "muxed.mp4"
            m = subprocess.run(["ffmpeg", "-y", "-i", str(cand), "-i", str(wav),
                                "-c:v", "copy", "-c:a", "aac", "-shortest", str(muxed)],
                               capture_output=True, text=True, timeout=600)
            if m.returncode == 0:
                cand = muxed
        import shutil
        shutil.copyfile(cand, out_mp4)
        return VideoClip(mp4_path=out_mp4, duration_s=dur)
