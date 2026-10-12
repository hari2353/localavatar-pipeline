"""SOLID ABCs. Heavy deps must be imported inside methods, never at top."""
import abc
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Script:
    title: str
    sections: list
    full_text: str


@dataclass
class AudioTrack:
    wav_path: Path
    duration_s: float


@dataclass
class VideoClip:
    mp4_path: Path
    duration_s: float


class IScriptProvider(abc.ABC):
    name: str
    @abc.abstractmethod
    def generate(self, niche: str, minutes: int, seed: int) -> Script: ...


class ITTSProvider(abc.ABC):
    name: str
    @abc.abstractmethod
    def synthesize(self, script: Script, out_wav: Path, voice_id: str = "") -> AudioTrack: ...


class IAvatarRenderer(abc.ABC):
    name: str
    @abc.abstractmethod
    def render(self, image: Path, audio: AudioTrack, out_mp4: Path) -> VideoClip: ...


class IBrollProvider(abc.ABC):
    name: str
    @abc.abstractmethod
    def generate(self, script: Script, out_dir: Path) -> list: ...


class IQualityGate(abc.ABC):
    name: str
    @abc.abstractmethod
    def review(self, clip: VideoClip) -> bool: ...


class ICompositor(abc.ABC):
    name: str
    @abc.abstractmethod
    def compose(self, avatar: VideoClip, audio: AudioTrack, broll: list, out_mp4: Path) -> VideoClip: ...
