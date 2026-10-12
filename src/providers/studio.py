"""Studio tier: REAL playable media using only preinstalled local tools.

- TemplateScriptProvider: structured niche script (~150 wpm, no LLM download)
- SapiTTSProvider: offline Windows SAPI voice -> wav (no network, no model)
- PillowFaceMaker: generates a host title-card PNG via Pillow
- FfmpegSlideshowRenderer: Ken Burns zoom over host PNG + narration -> real MP4
- CopyCompositor: final.mp4 = avatar clip (B-roll compositing lands in T5)
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..interfaces import (AudioTrack, IAvatarMaker, IAvatarRenderer, ICompositor,
                          IScriptProvider, ITTSProvider, Script, VideoClip)

STUDIO_ENGINES = {"template", "sapi", "pillow_face", "ffmpeg_slideshow"}

WORDS_PER_MIN = 115  # calibrated to SAPI David @Rate 0 (~117 wpm measured)


class TemplateScriptProvider(IScriptProvider):
    name = "template"

    def generate(self, niche: str, minutes: int, seed: int) -> Script:
        n = max(1, minutes)
        facts = [
            f"Fact one: the {niche} space rewards consistency over intensity. Small daily reps beat rare big pushes.",
            f"Fact two: most {niche} beginners skip fundamentals. Master the boring basics first and results compound.",
            f"Fact three: in {niche}, measure one number every day. What gets measured gets improved.",
            f"Fact four: study the top ten {niche} performers and copy their process, not their outcomes.",
            f"Fact five: every {niche} expert was once confused for a year. Confusion is the tuition, not a stop sign.",
        ]
        body = " ".join(facts[: max(2, min(len(facts), n + 1))])
        while len(body.split()) < n * WORDS_PER_MIN:
            body += " " + body
        words = body.split()[: n * WORDS_PER_MIN]
        full = (f"Welcome to your {niche} daily brief. " + " ".join(words)
                + f" That is your {niche} brief. Subscribe for tomorrow's edition.")
        return Script(title=f"{niche} daily brief", sections=["hook", "body", "cta"], full_text=full)


def _wav_duration(wav: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(wav)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0.0)


class SapiTTSProvider(ITTSProvider):
    """Offline narration via Windows System.Speech. en-US voices only (David/Zira)."""
    name = "sapi"

    def synthesize(self, script: Script, out_wav: Path, voice_id: str = "") -> AudioTrack:
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            txt = Path(td) / "script.txt"
            txt.write_text(script.full_text, encoding="utf-8")
            ps = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$s.Rate = 0; "
                f"$s.SetOutputToWaveFile('{out_wav}'); "
                f"$s.Speak([IO.File]::ReadAllText('{txt}')); $s.Dispose()"
            )
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               capture_output=True, text=True, timeout=600)
        if r.returncode != 0 or not out_wav.exists():
            raise RuntimeError(f"SAPI synthesis failed: {r.stderr[-500:]}")
        return AudioTrack(wav_path=out_wav, duration_s=_wav_duration(out_wav))


class PillowFaceMaker(IAvatarMaker):
    name = "pillow_face"

    def ensure(self, out_png: Path, seed: int = 42) -> Path:
        from PIL import Image, ImageDraw
        out_png.parent.mkdir(parents=True, exist_ok=True)
        if out_png.exists():
            return out_png
        img = Image.new("RGB", (1280, 720), (18 + seed % 40, 24, 48))
        d = ImageDraw.Draw(img)
        d.rectangle([440, 140, 840, 540], outline=(255, 200, 80), width=6)
        d.ellipse([560, 230, 720, 390], fill=(240, 200, 160))
        d.text((500, 580), f"AI HOST #{seed}", fill=(255, 255, 255))
        img.save(out_png)
        return out_png


class FfmpegSlideshowRenderer(IAvatarRenderer):
    name = "ffmpeg_slideshow"

    def render(self, image: Path, audio: AudioTrack, out_mp4: Path) -> VideoClip:
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        dur = max(2.0, audio.duration_s)
        vf = ("scale=2560:-2,zoompan=z='min(1.0+0.0008*on,1.25)':"
              "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=30,"
              "format=yuv420p")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(image),
               "-i", str(audio.wav_path), "-vf", vf, "-c:v", "libx264",
               "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
               "-t", f"{dur:.1f}", "-shortest", str(out_mp4)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        if r.returncode != 0 or not out_mp4.exists():
            raise RuntimeError(f"ffmpeg slideshow failed: {r.stderr[-800:]}")
        return VideoClip(mp4_path=out_mp4, duration_s=dur)


class CopyCompositor(ICompositor):
    name = "copy"

    def compose(self, avatar: VideoClip, audio: AudioTrack, broll: list, out_mp4: Path) -> VideoClip:
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(avatar.mp4_path, out_mp4)
        return VideoClip(mp4_path=out_mp4, duration_s=avatar.duration_s)


def write_srt(script: Script, duration_s: float, out_srt: Path, chunk_words: int = 9) -> Path:
    words = script.full_text.split()
    chunks = [" ".join(words[i:i + chunk_words]) for i in range(0, len(words), chunk_words)] or [script.title]
    per = max(0.5, duration_s / len(chunks))

    def ts(s: float) -> str:
        ms = int(s * 1000)
        return f"{ms // 3600000:02d}:{(ms // 60000) % 60:02d}:{(ms // 1000) % 60:02d},{ms % 1000:03d}"

    lines = []
    for i, c in enumerate(chunks):
        lines += [str(i + 1), f"{ts(i * per)} --> {ts((i + 1) * per)}", c, ""]
    out_srt.write_text("\n".join(lines), encoding="utf-8")
    return out_srt
