import base64
import hashlib
import io
import os
import random
import struct
import zipfile
import zlib

from challenges import FLAGS, SNAKE_LAYERS, SNAKE_PIN, xor_repeat

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "files")
FIXED_TIME = (2025, 1, 1, 0, 0, 0)


def _png_chunk(kind, data):
    return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _encode_png(width, height, rgb_rows, text_chunks):
    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0))
    for key, value in text_chunks:
        png += _png_chunk(b"tEXt", key.encode() + b"\x00" + value.encode())
    png += _png_chunk(b"IDAT", zlib.compress(b"".join(b"\x00" + row for row in rgb_rows), 9))
    png += _png_chunk(b"IEND", b"")
    return png


def _zip_bytes(name, data):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(zipfile.ZipInfo(name, FIXED_TIME), data, compress_type=zipfile.ZIP_DEFLATED)
    return buf.getvalue()


# 5x9 pixel font
_GLYPHS = {
    "a": ".....|.....|.###.|....#|.####|#...#|.####",
    "b": "#....|#....|####.|#...#|#...#|#...#|####.",
    "c": ".....|.....|.####|#....|#....|#....|.####",
    "d": "....#|....#|.####|#...#|#...#|#...#|.####",
    "e": ".....|.....|.###.|#...#|#####|#....|.####",
    "f": "..##.|.#...|####.|.#...|.#...|.#...|.#...",
    "g": ".....|.....|.####|#...#|#...#|#...#|.####|....#|.###.",
    "h": "#....|#....|####.|#...#|#...#|#...#|#...#",
    "i": "..#..|.....|.##..|..#..|..#..|..#..|.###.",
    "j": "...#.|.....|..##.|...#.|...#.|...#.|...#.|#..#.|.##..",
    "k": "#....|#....|#..#.|#.#..|##...|#.#..|#..#.",
    "l": ".##..|..#..|..#..|..#..|..#..|..#..|.###.",
    "m": ".....|.....|##.#.|#.#.#|#.#.#|#.#.#|#.#.#",
    "n": ".....|.....|####.|#...#|#...#|#...#|#...#",
    "o": ".....|.....|.###.|#...#|#...#|#...#|.###.",
    "p": ".....|.....|####.|#...#|#...#|#...#|####.|#....|#....",
    "q": ".....|.....|.####|#...#|#...#|#...#|.####|....#|....#",
    "r": ".....|.....|#.##.|##..#|#....|#....|#....",
    "s": ".....|.....|.####|#....|.###.|....#|####.",
    "t": ".#...|.#...|####.|.#...|.#...|.#..#|..##.",
    "u": ".....|.....|#...#|#...#|#...#|#..##|.##.#",
    "v": ".....|.....|#...#|#...#|#...#|.#.#.|..#..",
    "w": ".....|.....|#...#|#...#|#.#.#|#.#.#|.#.#.",
    "x": ".....|.....|#...#|.#.#.|..#..|.#.#.|#...#",
    "y": ".....|.....|#...#|#...#|#...#|#...#|.####|....#|.###.",
    "z": ".....|.....|#####|...#.|..#..|.#...|#####",
    "{": "..###|..#..|..#..|##...|..#..|..#..|..###",
    "}": "###..|..#..|..#..|...##|..#..|..#..|###..",
    "_": ".....|.....|.....|.....|.....|.....|.....|#####",
    ":": ".....|.....|..#..|.....|.....|..#..|.....",
    ".": ".....|.....|.....|.....|.....|.....|..#..",
    " ": ".....",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.",
    "1": "..#..|.##..|..#..|..#..|..#..|..#..|.###.",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####",
    "3": "####.|....#|....#|.###.|....#|....#|####.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.",
    "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": ".###.|#....|#....|####.|#...#|#...#|.###.",
    "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.",
    "9": ".###.|#...#|#...#|.####|....#|....#|.###.",
}


def _text_pixels(text, x0, y0, scale):
    unsupported = sorted(set(text) - set(_GLYPHS))
    if unsupported:
        raise SystemExit(f"The dark photo can't draw {unsupported} in {text!r}. "
                         "Use lowercase letters, digits, _ { } : . and spaces.")
    on = set()
    for i, ch in enumerate(text):
        for row, bits in enumerate(_GLYPHS[ch].split("|")):
            for col, bit in enumerate(bits):
                if bit == "#":
                    for dy in range(scale):
                        for dx in range(scale):
                            on.add((x0 + (i * 6 + col) * scale + dx, y0 + row * scale + dy))
    return on


def dark_photo_png():
    width, height = 960, 300
    text = _text_pixels(FLAGS["darkroom-1"], 60, 70, 5)
    text |= _text_pixels("next: read my comments", 60, 190, 4)
    rng = random.Random(7)
    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            v = rng.randint(0, 1) + (3 if (x, y) in text else 0)
            row += bytes((v + 1, v, v + 2))
        rows.append(bytes(row))
    # pad until the chunk's CRC doesn't start with a printable byte, so "strings" tools
    # don't glue a stray character onto the end of the base64
    for pad in range(64):
        comment = base64.b64encode(
            f"{FLAGS['darkroom-2']} - there's another file hidden inside this one{' ' * pad}".encode()).decode()
        crc = zlib.crc32(b"tEXtComment\x00" + comment.encode()) & 0xFFFFFFFF
        if not 32 <= crc >> 24 < 127:
            break
    png = _encode_png(width, height, rows, [
        ("Author", "unknown"),
        ("Software", "PhotoLab Recovery 1.3"),
        ("Comment", comment),
    ])
    note = f"found it\n{FLAGS['darkroom-3']}\n"
    # zip goes in an extra chunk just before IEND, so image tools can still open the photo
    hidden = _png_chunk(b"prIv", _zip_bytes("last_secret.txt", note.encode()))
    return png[:-12] + hidden + png[-12:]


def snake_stage1_py():
    message = f"{FLAGS['snake-1']}\nStage 2 needs a 4 digit PIN."
    secret = [ord(ch) ^ 0x2A for ch in message]
    return f'''#!/usr/bin/env python3
# Snake Lab - Stage 1

DEBUG = False

_SECRET = {secret}


def reveal():
    return "".join(chr(b ^ 0x2A) for b in _SECRET)


if __name__ == "__main__":
    if DEBUG:
        print(reveal())
    else:
        print("Access denied (debug is off)")
'''.encode()


def snake_stage2_py():
    message = f"{FLAGS['snake-2']}\nThe PIN was {SNAKE_PIN}. You need it for stage 3."
    vault = xor_repeat(message.encode(), SNAKE_PIN.encode()).hex()
    pin_hash = hashlib.sha256(SNAKE_PIN.encode()).hexdigest()
    return f'''#!/usr/bin/env python3
# Snake Lab - Stage 2: PIN lock
# 3 attempts only
import hashlib

PIN_HASH = "{pin_hash}"
_VAULT = bytes.fromhex("{vault}")


def unlock(pin):
    """Return the secret message if pin is correct, otherwise None."""
    if hashlib.sha256(pin.encode()).hexdigest() != PIN_HASH:
        return None
    key = pin.encode()
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(_VAULT)).decode()


if __name__ == "__main__":
    for attempt in range(3):
        result = unlock(input(f"Enter 4-digit PIN ({{3 - attempt}} tries left): ").strip())
        if result:
            print(result)
            break
        print("Wrong PIN.")
    else:
        print("Too many attempts.")
'''.encode()


def snake_stage3_txt():
    message = f"{FLAGS['snake-3']}\nThat's the last one."
    data = xor_repeat(message.encode(), SNAKE_PIN.encode())
    for _ in range(SNAKE_LAYERS):
        data = base64.b64encode(data)
    header = (
        "=== SNAKE LAB - STAGE 3 VAULT ===\n"
        "step 1 (sealing): XOR with the stage 2 PIN as text (e.g. b\"1234\"), key repeats\n"
        f"step 2 (wrapping): Base64, applied {SNAKE_LAYERS} times\n"
        "the data is the last line of this file\n"
        "---------------------------------\n"
    )
    return header.encode() + data + b"\n"


BUILDERS = {
    "dark_photo.png": dark_photo_png,
    "snake_stage1.py": snake_stage1_py,
    "snake_stage2.py": snake_stage2_py,
    "snake_stage3.txt": snake_stage3_txt,
}


def generate(force=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    built = []
    for name, builder in BUILDERS.items():
        path = os.path.join(OUT_DIR, name)
        if force or not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(builder())
            built.append(name)
    return built


if __name__ == "__main__":
    print("Generated:", ", ".join(generate(force=True)) or "nothing")
