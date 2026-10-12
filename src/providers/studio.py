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

STUDIO_ENGINES = {"template", "sapi", "pillow_face", "sd15_face", "ffmpeg_slideshow"}

WORDS_PER_MIN = 115  # calibrated to SAPI David @Rate 0 (~117 wpm measured)


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODELS = {"ollama_qwen": "qwen2.5:7b", "ollama_llama": "llama3.1:8b"}


def build_script_prompt(niche: str, word_budget: int, seed: int) -> str:
    return (
        f"You write a YouTube narration script about {niche} ({word_budget} words, seed {seed}). "
        "Rules: plain spoken sentences only, no markdown, no headings, no stage directions. "
        "Structure: 1 hook sentence, then facts each starting with 'Fact:', end with a subscribe call to action."
    )


class OllamaScriptProvider(IScriptProvider):
    """Local LLM script via Ollama HTTP API. Unloads the model afterwards to free VRAM."""

    def __init__(self, flag: str = "ollama_qwen"):
        self.flag = flag
        self.model = OLLAMA_MODELS[flag]
        self.name = flag

    def generate(self, niche: str, minutes: int, seed: int, word_budget: int = 0) -> Script:
        import json
        import urllib.request
        budget = word_budget or max(30, minutes * WORDS_PER_MIN)
        prompt = build_script_prompt(niche, budget, seed)
        body = json.dumps({"model": self.model, "prompt": prompt, "stream": False,
                           "options": {"num_predict": budget * 2, "temperature": 0.7}}).encode()
        req = urllib.request.Request(
            __import__("os").environ.get("LAP_OLLAMA_URL", OLLAMA_URL), data=body,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                text = json.load(r)["response"]
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"ollama request failed (is `ollama serve` running?): {e}")
        finally:
            self._unload()
        words = " ".join(text.split())
        if len(words.split()) > budget + 60:
            words = " ".join(words.split()[:budget])
        return Script(title=f"{niche} daily brief", sections=["hook", "body", "cta"], full_text=words)

    def _unload(self):
        import subprocess
        try:
            subprocess.run(["ollama", "stop", self.model], capture_output=True, timeout=120)
        except Exception:  # noqa: BLE001
            pass


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


class PiperTTSProvider(ITTSProvider):
    """Neural voice, offline, no model download beyond voices/piper/*.onnx (gitignored)."""
    name = "piper"
    DEFAULT_VOICE = "en_US-lessac-medium"

    def synthesize(self, script: Script, out_wav: Path, voice_id: str = "") -> AudioTrack:
        import sys
        ROOT = Path(__file__).resolve().parents[2]
        vdir = ROOT / "voices" / "piper"
        stem = voice_id if voice_id and (vdir / f"{voice_id}.onnx").exists() else self.DEFAULT_VOICE
        model = vdir / f"{stem}.onnx"
        if not model.exists():
            raise RuntimeError(f"piper voice missing: {model} (put .onnx+.json in voices/piper/)")
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        venv_piper = ROOT / ".venv" / "Scripts" / "piper.exe"
        exe = str(venv_piper) if venv_piper.exists() else "piper"
        r = subprocess.run([exe, "--model", str(model), "--output_file", str(out_wav)],
                           input=script.full_text.encode("utf-8"),
                           capture_output=True, timeout=900)
        if r.returncode != 0 or not out_wav.exists():
            raise RuntimeError(f"piper synth failed: {r.stderr[-400:]!r}")
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


class SD15FaceMaker(IAvatarMaker):
    """Photorealistic human face via local SD 1.5. Needs .venv + models/sd15 (see scripts/make_host_face.py)."""
    name = "sd15_face"

    def ensure(self, out_png: Path, seed: int = 42) -> Path:
        import subprocess
        import sys
        out_png.parent.mkdir(parents=True, exist_ok=True)
        if out_png.exists():
            return out_png
        ROOT = Path(__file__).resolve().parents[2]
        venv_py = ROOT / ".venv" / "Scripts" / "python.exe"
        py = str(venv_py) if venv_py.exists() else sys.executable
        r = subprocess.run([py, str(ROOT / "scripts" / "make_host_face.py"),
                            "--out", str(out_png), "--seed", str(seed)],
                           capture_output=True, text=True, timeout=3600)
        if r.returncode != 0 or not out_png.exists():
            raise RuntimeError(f"SD15 face gen failed (need .venv + model download): {r.stderr[-600:]}")
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
