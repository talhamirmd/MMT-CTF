import json
import os

FLAG_FORMAT = "flag{...}"


def _load_flags():
    raw = os.environ.get("CTF_FLAGS")
    if not raw:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flags.json")
        if not os.path.exists(path):
            raise SystemExit("No flags found. Copy flags.example.json to flags.json and edit it, "
                             "or set the CTF_FLAGS environment variable.")
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise SystemExit(f"Flags are not valid JSON: {exc}")


FLAGS = _load_flags()


def caesar(text, shift):
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + shift) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + shift) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


def vigenere(text, key):
    out, ki = [], 0
    for ch in text:
        if ch.isascii() and ch.isalpha():
            shift = ord(key[ki % len(key)].lower()) - 97
            base = 97 if ch.islower() else 65
            out.append(chr((ord(ch) - base + shift) % 26 + base))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


def xor_repeat(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


NOVA_ACCESS_CODE = "NOVA-7781-ALPHA"
SNAKE_PIN = "4071"
SNAKE_LAYERS = 20
GHOST_SHIFT = 11
GHOST_VIGENERE_KEY = "phantom"
GHOST_XOR_KEY = "spectre"
GHOST_TEXT_1 = caesar(
    "ghost to agent. if you can read this, you are one of us. "
    f"{FLAGS['ghost-1']} the keyword for the next transmission is {GHOST_VIGENERE_KEY}.", GHOST_SHIFT)
GHOST_TEXT_2 = vigenere(
    f"control to agent. well done. {FLAGS['ghost-2']} the final transmission is xor encrypted "
    f"with the repeating key {GHOST_XOR_KEY}, written as hex.", GHOST_VIGENERE_KEY)
GHOST_TEXT_3 = xor_repeat(f"mission complete. ghost signing off. {FLAGS['ghost-3']}".encode(),
                          GHOST_XOR_KEY.encode()).hex()


CHALLENGES = []

MISSIONS = [
    {
        "id": "nova",
        "name": "NovaTech",
        "category": "Web",
        "difficulty": "Easy",
        "tagline": "A company website with a few things the developers forgot to clean up.",
        "phases": [
            {
                "id": "nova-1",
                "name": "Hidden element",
                "points": 50,
                "description": "<p>This is NovaTech's website. The first flag is in the page somewhere, but you won't see it on screen.</p>",
                "link": "/chal/m/nova",
                "hints": [
                    "Right-click anywhere on the page and choose Inspect (or press F12). This opens the Elements panel.",
                    "Some elements are in the page but hidden with the <code>hidden</code> attribute. "
                    "Expand the <code>&lt;footer&gt;</code> and look around.",
                    "View Source (Ctrl+U) won't show it, because JavaScript adds the text after the page loads. "
                    "In the Elements panel, find the element with the id <code>employee-of-the-month</code>.",
                ],
            },
            {
                "id": "nova-2",
                "name": "Staff portal",
                "points": 75,
                "description": "<p>The first flag mentions a staff portal. It asks for an access code you don't have. Find a way in.</p>",
                "link": "/chal/m/nova/staff",
                "hints": [
                    "Open DevTools (F12), switch to the Console tab, then reload the page.",
                    "One of the console messages is Base64. Decode it with CyberChef, or type "
                    "<code>atob(\"...\")</code> into the console.",
                    "Type the decoded access code into the login form exactly as it appears, dashes included.",
                ],
            },
            {
                "id": "nova-3",
                "name": "The vault",
                "points": 100,
                "description": "<p>You're logged in as staff now, but the vault only opens for admin. How does the site know which one you are?</p>",
                "link": "/chal/m/nova/vault",
                "hints": [
                    "The website remembers who you are with a small piece of data stored in your browser.",
                    "DevTools > Application tab (Chrome/Edge) or Storage tab (Firefox) > Cookies. "
                    "Look for one called <code>clearance</code>.",
                    "Double-click the cookie's value, change <code>staff</code> to <code>admin</code>, then reload the vault.",
                ],
            },
        ],
    },
    {
        "id": "darkroom",
        "name": "Dark Room",
        "category": "Forensics",
        "difficulty": "Easy",
        "tagline": "All three flags are in one image file. You only need a browser.",
        "phases": [
            {
                "id": "darkroom-1",
                "name": "Too dark",
                "points": 50,
                "description": "<p>This photo came off a seized SD card. It looks completely black. Download it and take a closer look.</p>",
                "link": "/chal/m/darkroom",
                "hints": [
                    "The pixels aren't completely black. The text is just a few shades lighter than the background.",
                    "Open <a href=\"https://gchq.github.io/CyberChef/\" target=\"_blank\" rel=\"noopener\">CyberChef</a> "
                    "(it's a website, nothing to install) and drag the photo into the Input box.",
                    "Search for the Normalise Image operation and drag it into the Recipe. It stretches the darkest and lightest "
                    "pixels to full black and full white. Read both lines.",
                ],
            },
            {
                "id": "darkroom-2",
                "name": "Comments",
                "points": 75,
                "description": "<p>The photo told you to read the comments. Image files can store text next to the pixels.</p>",
                "link": "/chal/m/darkroom",
                "hints": [
                    "Load the photo into CyberChef again. This time you want the readable text inside the file, not the picture.",
                    "The Strings operation lists every piece of readable text. Set Minimum length to 20.",
                    "One line is a long mix of letters and numbers. That's Base64: decode it with From Base64.",
                ],
            },
            {
                "id": "darkroom-3",
                "name": "Hidden file",
                "points": 100,
                "description": "<p>The comment says there's another file hidden inside the photo. Find it and open it.</p>",
                "link": "/chal/m/darkroom",
                "hints": [
                    "Files can be tucked inside other files. Tools that look for them are called file carvers.",
                    "CyberChef's Extract Files operation scans a file for other files hidden inside it.",
                    "It finds a .zip. Click Move to input on that line, then use the Unzip operation and click the file name.",
                ],
            },
        ],
    },
    {
        "id": "snake",
        "name": "Snake Lab",
        "category": "Misc",
        "difficulty": "Medium",
        "tagline": "Three Python files. You'll need Python 3 installed.",
        "phases": [
            {
                "id": "snake-1",
                "name": "Debug mode",
                "difficulty": "Easy",
                "points": 50,
                "description": "<p>Download <code>snake_stage1.py</code> and run it with <code>python snake_stage1.py</code>. It won't print the flag unless you change something.</p>",
                "link": "/chal/m/snake/1",
                "hints": [
                    "Install Python 3 from python.org if you don't have it. Open a terminal in the folder with the file "
                    "and run <code>python snake_stage1.py</code>.",
                    "Open the file in a text editor (Notepad, VS Code, IDLE). What decides whether the flag is printed?",
                    "Change <code>DEBUG = False</code> to <code>DEBUG = True</code>, save, and run it again. "
                    "Read the line under the flag too.",
                ],
            },
            {
                "id": "snake-2",
                "name": "PIN",
                "points": 100,
                "description": "<p>This one wants a 4 digit PIN and gives you 3 tries. You have the code though, so nothing stops you from trying all of them.</p>",
                "link": "/chal/m/snake/2",
                "hints": [
                    "Read the <code>unlock()</code> function. It returns the secret for the right PIN and "
                    "<code>None</code> for anything else.",
                    "Write a loop that tries every PIN from 0000 to 9999. <code>f\"{i:04d}\"</code> turns 7 into "
                    "<code>\"0007\"</code>.",
                    "Replace the <code>if __name__ == \"__main__\":</code> block at the bottom with:"
                    "<pre>for i in range(10000):\n    pin = f\"{i:04d}\"\n    secret = unlock(pin)\n"
                    "    if secret:\n        print(pin, secret)\n        break</pre>You'll need the PIN for stage 3.",
                ],
            },
            {
                "id": "snake-3",
                "name": "Layers",
                "points": 150,
                "description": f"<p>The last file was XORed with the PIN from stage 2 and then base64 encoded {SNAKE_LAYERS} times. Write a short script to get it back.</p>",
                "link": "/chal/m/snake/3",
                "hints": [
                    "Read the file header: it tells you the order. Undo the steps in reverse: Base64-decode "
                    f"{SNAKE_LAYERS} times first, then XOR.",
                    "The data is the last line of the file: "
                    "<code>data = open(\"snake_stage3.txt\").read().strip().splitlines()[-1].encode()</code>. "
                    "<code>base64.b64decode()</code> returns bytes, so you can feed its output straight back in with "
                    f"<code>for _ in range({SNAKE_LAYERS}):</code>.",
                    "XOR each byte with the PIN's characters in turn:"
                    "<pre>key = b\"0000\"   # your PIN from stage 2\n"
                    "print(bytes(b ^ key[i % len(key)] for i, b in enumerate(data)).decode())</pre>",
                ],
            },
        ],
    },
    {
        "id": "ghost",
        "name": "Ghost Signal",
        "category": "Crypto",
        "difficulty": "Medium",
        "tagline": "Three intercepted messages. Each one has the key for the next.",
        "phases": [
            {
                "id": "ghost-1",
                "name": "Message 1",
                "difficulty": "Easy",
                "points": 50,
                "description": "<p>We picked up this message from a station calling itself GHOST. It looks like every letter was shifted by the same amount. Besides the flag, it has the key for message 2.</p>",
                "link": "/chal/m/ghost/1",
                "hints": [
                    "This is a Caesar cipher. There are only 25 possible shifts, so you can just try them all.",
                    "CyberChef's ROT13 operation has an Amount field. Change it until the text becomes "
                    "readable, or use dcode.fr's Caesar tool in brute-force mode.",
                    "In Python:<pre>for s in range(26):\n"
                    "    print(s, \"\".join(chr((ord(c) - 97 - s) % 26 + 97) if c.islower() else c for c in msg))</pre>",
                ],
            },
            {
                "id": "ghost-2",
                "name": "Message 2",
                "points": 100,
                "description": "<p>The second message uses a keyword cipher. Message 1 told you the keyword.</p>",
                "link": "/chal/m/ghost/2",
                "hints": [
                    "This is the Vigenère cipher, and the keyword from transmission 1 is its key.",
                    "CyberChef has a Vigenère Decode operation. Paste the text and enter the keyword.",
                    "Only letters are shifted; spaces, punctuation and <code>{ } _</code> stay the same. "
                    "If it starts with <code>control</code>, you're on the right track.",
                ],
            },
            {
                "id": "ghost-3",
                "name": "Message 3",
                "points": 150,
                "description": "<p>The last message is hex. Message 2 told you how it was encrypted.</p>",
                "link": "/chal/m/ghost/3",
                "hints": [
                    "Hex is bytes written as text. Turn it back with CyberChef's From Hex, or "
                    "<code>bytes.fromhex()</code> in Python.",
                    "Repeating-key XOR: byte 1 is XORed with the key's 1st letter, byte 2 with the 2nd, and so on, "
                    "starting over when you run out of key.",
                    "CyberChef: From Hex > XOR (key = the word from transmission 2, format UTF8). Or in Python:"
                    "<pre>key = b\"...\"\n"
                    "print(bytes(b ^ key[i % len(key)] for i, b in enumerate(bytes.fromhex(ct))).decode())</pre>",
                ],
            },
        ],
    },
]

for _m in MISSIONS:
    _prev = None
    for _n, _p in enumerate(_m["phases"], 1):
        _p.update(mission=_m["id"], phase=_n, requires=_prev and _prev["id"], category=_m["category"])
        _p.setdefault("difficulty", _m["difficulty"])
        if _prev:
            _prev["next"] = _p["id"]
        _prev = _p
        CHALLENGES.append(_p)

MISSIONS_BY_ID = {m["id"]: m for m in MISSIONS}

_missing = [c["id"] for c in CHALLENGES if c["id"] not in FLAGS]
if _missing:
    raise SystemExit("Missing flags for: " + ", ".join(_missing))

for _c in CHALLENGES:
    _c["flag"] = FLAGS[_c["id"]]
    _c.setdefault("next", None)

CHALLENGES_BY_ID = {c["id"]: c for c in CHALLENGES}
