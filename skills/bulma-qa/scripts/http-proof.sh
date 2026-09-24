#!/usr/bin/env bash
# Render an HTTP request/response transcript to a PNG still for QA evidence.
# Usage:
#   http-proof.sh --out path.png [--title TEXT]
#     [--from file | --method M --url URL --status N
#      (--body TEXT | --body-file F)]
#
# python3 is required. No browser.
set -euo pipefail

print_usage() {
  sed -n '2,8p' "$0" | sed 's/^# \?//'
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  print_usage
  exit 0
fi

command -v python3 >/dev/null || {
  echo "python3 required for http-proof.sh" >&2
  exit 1
}

exec python3 - "$@" <<'PY'
import argparse
import struct
import sys
import zlib
from pathlib import Path


def bits(*rows: str) -> int:
    n = 0
    for row in rows:
        for ch in row:
            n = (n << 1) | (1 if ch == "1" else 0)
    return n


# 3x5 glyphs, bit 14 is top-left. Lowercase maps to these keys.
GLYPHS = {
    " ": bits("000", "000", "000", "000", "000"),
    "0": bits("111", "101", "101", "101", "111"),
    "1": bits("010", "110", "010", "010", "111"),
    "2": bits("111", "001", "111", "100", "111"),
    "3": bits("111", "001", "111", "001", "111"),
    "4": bits("101", "101", "111", "001", "001"),
    "5": bits("111", "100", "111", "001", "111"),
    "6": bits("111", "100", "111", "101", "111"),
    "7": bits("111", "001", "010", "010", "010"),
    "8": bits("111", "101", "111", "101", "111"),
    "9": bits("111", "101", "111", "001", "111"),
    "A": bits("010", "101", "111", "101", "101"),
    "B": bits("110", "101", "110", "101", "110"),
    "C": bits("111", "100", "100", "100", "111"),
    "D": bits("110", "101", "101", "101", "110"),
    "E": bits("111", "100", "110", "100", "111"),
    "F": bits("111", "100", "110", "100", "100"),
    "G": bits("111", "100", "101", "101", "111"),
    "H": bits("101", "101", "111", "101", "101"),
    "I": bits("111", "010", "010", "010", "111"),
    "J": bits("001", "001", "001", "101", "111"),
    "K": bits("101", "101", "110", "101", "101"),
    "L": bits("100", "100", "100", "100", "111"),
    "M": bits("101", "111", "111", "101", "101"),
    "N": bits("101", "111", "111", "111", "101"),
    "O": bits("111", "101", "101", "101", "111"),
    "P": bits("111", "101", "111", "100", "100"),
    "Q": bits("111", "101", "101", "111", "001"),
    "R": bits("111", "101", "110", "101", "101"),
    "S": bits("111", "100", "111", "001", "111"),
    "T": bits("111", "010", "010", "010", "010"),
    "U": bits("101", "101", "101", "101", "111"),
    "V": bits("101", "101", "101", "101", "010"),
    "W": bits("101", "101", "111", "111", "101"),
    "X": bits("101", "101", "010", "101", "101"),
    "Y": bits("101", "101", "010", "010", "010"),
    "Z": bits("111", "001", "010", "100", "111"),
    "-": bits("000", "000", "111", "000", "000"),
    "_": bits("000", "000", "000", "000", "111"),
    "=": bits("000", "111", "000", "111", "000"),
    "+": bits("000", "010", "111", "010", "000"),
    "/": bits("001", "001", "010", "100", "100"),
    "\\": bits("100", "100", "010", "001", "001"),
    ":": bits("000", "010", "000", "010", "000"),
    ";": bits("000", "010", "000", "010", "100"),
    ".": bits("000", "000", "000", "000", "010"),
    ",": bits("000", "000", "000", "010", "100"),
    "?": bits("111", "001", "010", "000", "010"),
    "!": bits("010", "010", "010", "000", "010"),
    "'": bits("010", "010", "000", "000", "000"),
    '"': bits("101", "101", "000", "000", "000"),
    "`": bits("010", "001", "000", "000", "000"),
    "@": bits("111", "101", "101", "100", "111"),
    "#": bits("101", "111", "101", "111", "101"),
    "$": bits("010", "111", "110", "011", "010"),
    "%": bits("101", "001", "010", "100", "101"),
    "&": bits("010", "101", "010", "101", "011"),
    "*": bits("000", "101", "010", "101", "000"),
    "(": bits("010", "100", "100", "100", "010"),
    ")": bits("010", "001", "001", "001", "010"),
    "[": bits("110", "100", "100", "100", "110"),
    "]": bits("011", "001", "001", "001", "011"),
    "{": bits("011", "010", "110", "010", "011"),
    "}": bits("110", "010", "011", "010", "110"),
    "<": bits("001", "010", "100", "010", "001"),
    ">": bits("100", "010", "001", "010", "100"),
    "|": bits("010", "010", "010", "010", "010"),
    "~": bits("000", "011", "110", "000", "000"),
    "^": bits("010", "101", "000", "000", "000"),
}

UNKNOWN = bits("101", "010", "101", "010", "101")
SCALE = 3
GAP_X = 2
GAP_Y = 4
PAD = 16
COL_W = 3 * SCALE + GAP_X
ROW_H = 5 * SCALE + GAP_Y
MAX_COLS = 88
MAX_ROWS = 48
BG = (255, 255, 255)
FG = (20, 20, 20)


def glyph_for(ch: str) -> int:
    if ch in GLYPHS:
        return GLYPHS[ch]
    up = ch.upper()
    if up in GLYPHS:
        return GLYPHS[up]
    if ch in "\t":
        return GLYPHS[" "]
    return UNKNOWN


def wrap(text: str) -> list[str]:
    lines: list[str] = []
    parts = text.splitlines() or [""]
    for raw in parts:
        if len(raw) <= MAX_COLS:
            lines.append(raw)
            continue
        for i in range(0, len(raw), MAX_COLS):
            lines.append(raw[i : i + MAX_COLS])
    return lines[:MAX_ROWS]


def plot(pixels: list[tuple[int, int, int]], w: int, x: int, y: int, rgb):
    if 0 <= x < w and 0 <= y < (len(pixels) // w):
        pixels[y * w + x] = rgb


def draw_char(pixels, w, origin_x, origin_y, ch):
    g = glyph_for(ch)
    for r in range(5):
        for c in range(3):
            bit = (g >> (14 - (r * 3 + c))) & 1
            if not bit:
                continue
            for dy in range(SCALE):
                for dx in range(SCALE):
                    plot(
                        pixels,
                        w,
                        origin_x + c * SCALE + dx,
                        origin_y + r * SCALE + dy,
                        FG,
                    )


def write_png(path: Path, w: int, h: int, pixels: list[tuple[int, int, int]]):
    raw = bytearray()
    i = 0
    for _y in range(h):
        raw.append(0)
        for _x in range(w):
            r, g, b = pixels[i]
            raw.extend((r, g, b))
            i += 1

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def compose_text(args) -> str:
    if args.from_file:
        data = Path(args.from_file).read_text(encoding="utf-8", errors="replace")
        if args.title:
            return f"{args.title}\n\n{data}"
        return data
    lines = []
    if args.title:
        lines.append(args.title)
    req = " ".join(p for p in (args.method, args.url) if p).strip()
    if req:
        lines.append(req)
    if args.status:
        lines.append(f"HTTP {args.status}")
    body = args.body or ""
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8", errors="replace")
    if body:
        if lines:
            lines.append("")
        lines.append(body[:6000])
    return "\n".join(lines).strip() or "HTTP proof"


def main() -> int:
    p = argparse.ArgumentParser(prog="http-proof.sh")
    p.add_argument("--out", required=True)
    p.add_argument("--title")
    p.add_argument("--from", dest="from_file")
    p.add_argument("--method")
    p.add_argument("--url")
    p.add_argument("--status")
    p.add_argument("--body")
    p.add_argument("--body-file")
    args = p.parse_args(sys.argv[1:])
    if not args.from_file and not (args.method or args.url or args.status or args.body or args.body_file):
        p.error("pass --from FILE or --method/--url/--status/--body")
    text = compose_text(args)
    rows = wrap(text)
    cols = max((len(r) for r in rows), default=1)
    w = max(PAD * 2 + cols * COL_W, 320)
    h = max(PAD * 2 + len(rows) * ROW_H, 120)
    pixels = [BG] * (w * h)
    for ri, row in enumerate(rows):
        y = PAD + ri * ROW_H
        for ci, ch in enumerate(row):
            draw_char(pixels, w, PAD + ci * COL_W, y, ch)
    write_png(Path(args.out), w, h, pixels)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"http-proof.sh: {exc}", file=sys.stderr)
        raise SystemExit(1)
PY
