"""Draws the Lumen mark (a glowing projector lens) as PNG, with no dependencies.

write_icon(path)  512px square add-on icon on the dark Lumen background
write_logo(path)  240px mark on a transparent background, for the home screen
"""
import struct
import zlib
from pathlib import Path

BG = (0x0B, 0x0D, 0x12)
RING = (0xE8, 0x50, 0x5B)
CORE = (0xF2, 0x6B, 0x70)
SHINE = (0xFF, 0xC2, 0xB4)


def _png(path, size, rows):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(bytes(rows), 9))
    data += chunk(b"IEND", b"")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _over(dst, colour, alpha):
    """Composite a colour at the given alpha over an (r, g, b, a) pixel."""
    r, g, b, a = dst
    out_a = alpha + a * (1 - alpha)
    if out_a <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    mix = lambda new, old: (new * alpha + old * a * (1 - alpha)) / out_a
    return (mix(colour[0], r), mix(colour[1], g), mix(colour[2], b), out_a)


def _render(size, scale, background, glow):
    half = size / 2
    centre = (size - 1) / 2
    px = half / scale  # pixels per unit of normalised radius

    def cover(edge, d):  # anti-aliased "inside radius" coverage
        return min(1.0, max(0.0, 0.5 + (edge - d) * px))

    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            d = ((x - centre) ** 2 + (y - centre) ** 2) ** 0.5 / half * scale
            pixel = (*background, 1.0) if background else (0.0, 0.0, 0.0, 0.0)
            if glow and d > 0.45:
                pixel = _over(pixel, RING, max(0.0, 1 - (d - 0.45) / 0.5) ** 2 * glow)
            pixel = _over(pixel, RING, cover(0.50, d) - cover(0.41, d))
            core = cover(0.32, d)
            if core:
                # highlight sits up and to the left, like light catching a lens
                hx = (x - centre) / half * scale + 0.10
                hy = (y - centre) / half * scale + 0.10
                shine = max(0.0, 1 - (hx * hx + hy * hy) ** 0.5 / 0.30)
                colour = tuple(c + (s - c) * shine for c, s in zip(CORE, SHINE))
                pixel = _over(pixel, colour, core)
            rows += bytes(int(round(c)) for c in pixel[:3]) + bytes((int(round(pixel[3] * 255)),))
    return rows


def write_icon(path, size=512):
    _png(path, size, _render(size, 0.80, BG, 0.55))


def write_logo(path, size=240):
    _png(path, size, _render(size, 0.52, None, 0.0))
