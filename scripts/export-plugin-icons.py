#!/usr/bin/env python3
"""Export the existing LingMind logo for the cloud App's 10 KB PNG limit."""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "plugins/lingmind/assets/lingmind-logo.png"
other = ROOT / "plugins/lingmind-operator/assets/lingmind-logo.png"
if source.read_bytes() != other.read_bytes():
    raise ValueError("The two plugins must use the same original LingMind logo")
original = Image.open(source).convert("RGBA")
bounds = original.getbbox()
if bounds is None:
    raise ValueError("The LingMind logo is empty")
# Remove source-canvas whitespace, then leave a 12 px visual safety margin.
image = ImageOps.contain(original.crop(bounds), (232, 232), Image.Resampling.LANCZOS)
icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
icon.paste(image, ((256 - image.width) // 2, (256 - image.height) // 2))
buffer = BytesIO()
# Six-bit color channels preserve the gradient and full alpha while fitting
# the App upload limit without palette banding.
red, green, blue, alpha = icon.split()
channels = tuple(
    channel.point(lambda value: min(255, round(value / 4) * 4))
    for channel in (red, green, blue)
)
icon = Image.merge("RGBA", channels + (alpha,))
icon.save(buffer, format="PNG", optimize=True, compress_level=9)
raw = buffer.getvalue()
if len(raw) > 10_000:
    raise ValueError("Icon exceeds the cloud App upload limit; do not change the original logo")
for name in ("lingmind", "lingmind-operator"):
    target = ROOT / "plugins" / name / "assets/lingmind-logo-256.png"
    target.write_bytes(raw)
    print(f"{target}: 256x256 RGBA PNG, {len(raw)} bytes")
