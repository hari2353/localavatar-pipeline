"""Post-production: burned-in subtitles and brand-aware auto thumbnails —
the AutoShorts/Revid/Captions table stakes this repo's README listed as
"still open". Flag-gated; OFF behavior changes nothing.

Brand colors are clamped to safe hex and the thumbnail is a bounded
1280x720 YouTube-ready frame. The mock/CI path copies bytes (deterministic);
the real path shells to ffmpeg with the SRT burned in.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

HEX_ALPHABET = set("0123456789abcdefABCDEF")
_MAX_TITLE_SCALE = 3.0
_MIN_TITLE_SCALE = 0.5


@dataclass
class Brand:
    """Every-episode consistency (HeyGen's brand kit, minimal)."""

    handle: str = ""
    accent: str = "#22c55e"
    title_scale: float = 1.0

    def __post_init__(self) -> None:
        self.accent = self._clamp_hex(self.accent)
        self.title_scale = max(
            _MIN_TITLE_SCALE, min(_MAX_TITLE_SCALE, float(self.title_scale))
        )

    @staticmethod
    def _clamp_hex(value: str) -> str:
        value = str(value).strip().lstrip("#")
        if len(value) == 3 and all(c in HEX_ALPHABET for c in value):
            value = "".join(c * 2 for c in value)
        if len(value) == 6 and all(c in HEX_ALPHABET for c in value):
            return f"#{value.lower()}"
        return "#000000"


def brand_from(cfg_brand: dict | None) -> Brand:
    cfg_brand = cfg_brand or {}
    return Brand(
        handle=str(cfg_brand.get("handle", "")),
        accent=str(cfg_brand.get("accent", Brand.accent)),
        title_scale=float(cfg_brand.get("title_scale", 1.0)),
    )


def burn_subtitles(video: Path, srt: Path, out: Path, *, font_size: int = 48) -> Path:
    """Burn ``srt`` into ``video``. Real path: ffmpeg subtitles filter;
    mock path (mock-tier bytes or ffmpeg absent): deterministic copy that
    keeps A/V so CI and offline use stay honest."""
    out.parent.mkdir(parents=True, exist_ok=True)
    header = video.read_bytes()[:8]
    is_real_mp4 = b"ftyp" in header  # mock bytes are not a real container
    if not is_real_mp4 or shutil.which("ffmpeg") is None:
        shutil.copyfile(video, out)
        return out
    escaped = str(srt).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-vf",
            f"subtitles={escaped}:force_style='FontSize={font_size}'",
            "-c:a",
            "copy",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def make_thumbnail(
    host_png: Path, title: str, out: Path, brand: Brand | None = None
) -> Path:
    """1280x720 thumbnail: the host frame, an accent bar, the handle and the
    (wrapped, bounded) episode title. Pillow-only, CPU, deterministic."""
    from PIL import Image, ImageDraw, ImageFont

    brand = brand or Brand()
    width, height = 1280, 720
    canvas = Image.new("RGB", (width, height), (16, 18, 24))
    try:
        with Image.open(host_png) as host:
            host = host.convert("RGB")
            cover = max(width / host.width, height / host.height)
            host = host.resize((int(host.width * cover), int(host.height * cover)))
            canvas.paste(host.crop((0, 0, width, height)), (0, 0))
    except Exception:  # placeholder/mock host bytes: brand card without a face
        pass
    draw = ImageDraw.Draw(canvas)
    rgb = tuple(int(brand.accent[i : i + 2], 16) for i in (1, 3, 5))
    draw.rectangle([0, height - 24, width, height], fill=rgb)
    if brand.handle:
        draw.text(
            (width - 24, height - 56), brand.handle, fill=(240, 240, 240), anchor="ra"
        )
    size = max(28, min(72, int(48 * brand.title_scale)))
    try:
        font: ImageFont.ImageFont | None = ImageFont.load_default(size)
    except TypeError:  # pillow < 10.1: no size arg
        font = ImageFont.load_default()
    words, lines, line = title.split(), [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) > width - 96 and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    lines = lines[:3]  # bounded: at most three title lines
    y = 48
    for line_text in lines:
        draw.text((48, y), line_text, fill=(255, 255, 255), font=font)
        y += int(size * 1.25)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "JPEG", quality=88)
    return out
