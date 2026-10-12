"""Offline fakes: let the whole loop run end-to-end with zero GPU/downloads."""
from pathlib import Path

from ..interfaces import (AudioTrack, IAvatarMaker, IBrollProvider, IAvatarRenderer, ICompositor,
                          IQualityGate, IScriptProvider, ITTSProvider, Script, VideoClip)


class MockScript(IScriptProvider):
    name = "mock"
    def generate(self, niche: str, minutes: int, seed: int) -> Script:
        words = max(30, minutes * 150)
        return Script(title=f"{niche} daily brief",
                      sections=["hook", "body", "cta"],
                      full_text=(" ".join([f"{niche}-fact-{seed}"] * words))[: words * 8])


class MockTTS(ITTSProvider):
    name = "mock"
    def synthesize(self, script: Script, out_wav: Path, voice_id: str = "") -> AudioTrack:
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        out_wav.write_bytes(b"mock-wav:" + script.title.encode())
        return AudioTrack(wav_path=out_wav, duration_s=180.0)


class MockAvatar(IAvatarRenderer):
    name = "mock"
    def render(self, image: Path, audio: AudioTrack, out_mp4: Path) -> VideoClip:
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        out_mp4.write_bytes(b"mock-avatar")
        return VideoClip(mp4_path=out_mp4, duration_s=audio.duration_s)


class NullBroll(IBrollProvider):
    name = "none"
    def generate(self, script: Script, out_dir: Path) -> list:
        return []


class MockBroll(IBrollProvider):
    name = "mock"
    def generate(self, script: Script, out_dir: Path) -> list:
        p = out_dir / "broll.txt"
        p.write_text("mock-broll")
        return [str(p)]


class PassThroughGate(IQualityGate):
    name = "off"
    def review(self, clip: VideoClip) -> bool:
        return True


class MockAvatarMaker(IAvatarMaker):
    """Dev/CI double: reuses the user's PNG, or writes a placeholder if missing."""
    name = "mock"
    def ensure(self, out_png: Path, seed: int = 42) -> Path:
        out_png.parent.mkdir(parents=True, exist_ok=True)
        if not out_png.exists():
            out_png.write_bytes(b"mock-face-seed-%d" % seed)
        return out_png


class ExistingFileAvatarMaker(IAvatarMaker):
    """Flag `none`: strict mode, user must supply their own host PNG."""
    name = "none"
    def ensure(self, out_png: Path, seed: int = 42) -> Path:
        if not out_png.exists():
            raise FileNotFoundError(f"host image missing: {out_png} (supply your own or set avatar_maker: mock/sd15_local)")
        return out_png
