# Walkthroughs for every phase. Screenshots are in static/guide/ and were taken with
# placeholder flags, so they show flag{...}. The real flag is added when the page is shown.

GUIDES = {
    "nova-1": {
        "learn": [
            "The difference between the page source (what the server sends) and the DOM (what the browser builds after JavaScript runs).",
            "How to use the Elements panel in DevTools to look at everything on a page, including things that are hidden.",
            "Hiding something with CSS or the <code>hidden</code> attribute is not security. If it was sent to your browser, you can read it.",
        ],
        "steps": [
            ("Open the challenge. It's a normal company homepage and there's nothing interesting on screen.", "nova-1-1.png"),
            ("Try <b>View Source</b> first (Ctrl+U) and scroll to the bottom. There's an empty <code>&lt;div id=\"employee-of-the-month\"&gt;</code> "
             "and a script with a long list of numbers. The text isn't in the source. The script builds it after the page loads, "
             "which is why View Source doesn't show it.", "nova-1-2.png"),
            ("Press <b>F12</b> to open DevTools and go to the <b>Elements</b> tab. This shows the page as it is right now, after the "
             "script ran. Expand <code>&lt;footer&gt;</code> and you'll find the div filled in. It has the <code>hidden</code> attribute "
             "so it doesn't show on the page, but it's there. It contains the flag and says the staff portal moved to "
             "<code>/chal/m/nova/staff</code>, which is phase 2.", "nova-1-3.png"),
            ("Copy the flag from the Elements panel and submit it.", None),
        ],
    },
    "nova-2": {
        "learn": [
            "Debug messages that developers write with <code>console.log</code> are sent to every visitor, not just the developer.",
            "Base64 is an encoding, not encryption. Anyone can turn it back into the original text.",
            "How to run JavaScript yourself in the browser console.",
        ],
        "steps": [
            ("Go to the staff portal. It asks for an access code you don't have.", "nova-2-1.png"),
            ("Open DevTools (F12), click the <b>Console</b> tab and reload the page. Two messages show up. The second one says "
             "<i>default access code (b64)</i> followed by a string of letters. b64 means Base64.", "nova-2-2.png"),
            ("Decode it right there: type <code>atob(\"...\")</code> with the string inside the quotes and press Enter. "
             "<code>atob</code> is the browser's built-in Base64 decoder. You get <code>NOVA-7781-ALPHA</code>. "
             "CyberChef's <i>From Base64</i> works too.", "nova-2-3.png"),
            ("Type the code into the login form and sign in. The page shows the flag and a note that the vault is at "
             "<code>/chal/m/nova/vault</code>.", "nova-2-4.png"),
        ],
    },
    "nova-3": {
        "learn": [
            "What cookies are and how websites use them to remember who you are.",
            "Cookies live in your browser, so you can read and change them.",
            "A server should never trust something like a role or permission level stored in a cookie.",
        ],
        "steps": [
            ("Open the vault. It says your clearance is <b>staff</b> and denies access.", "nova-3-1.png"),
            ("Where does \"staff\" come from? When you logged in, the site saved a cookie. Open DevTools, go to "
             "<b>Application</b> &gt; <b>Cookies</b> and click the site's address. There's a cookie called "
             "<code>clearance</code> with the value <code>staff</code>. (In Firefox it's the <b>Storage</b> tab.)", "nova-3-2.png"),
            ("Double-click the value, change it to <code>admin</code> and press Enter.", "nova-3-3.png"),
            ("Reload the vault. The server reads the cookie, sees admin and lets you in.", "nova-3-4.png"),
        ],
    },
    "darkroom-1": {
        "learn": [
            "Every pixel is stored as numbers from 0 to 255. A picture that looks black can still hold dark shades your eyes can't tell apart.",
            "Stretching the contrast of an image (normalising) makes those hidden shades visible.",
            "How to load a file into CyberChef, a free website you'll use for the whole mission.",
        ],
        "steps": [
            ("Open the challenge and download <code>dark_photo.png</code>.", "darkroom-1-1.png"),
            ("Go to <a href=\"https://gchq.github.io/CyberChef/\" target=\"_blank\" rel=\"noopener\">CyberChef</a>. It's a website, "
             "there's nothing to install or sign up for. Drag the photo into the <b>Input</b> box (top right). Then type "
             "<b>normalise</b> into the search box on the left.", "darkroom-1-2.png"),
            ("Drag <b>Normalise Image</b> into the Recipe. It takes the darkest pixel and makes it black, takes the lightest pixel and "
             "makes it white, and spreads everything in between. The text was only 3 shades brighter than the background, and now "
             "you can read it in the Output box. The first line is the flag. The second line says <i>next: read my comments</i>, "
             "which is the hint for phase 2.", "darkroom-1-3.png"),
        ],
    },
    "darkroom-2": {
        "learn": [
            "Files carry extra information next to their main content, called metadata. PNG files can store text like a comment.",
            "Finding the readable text hidden inside any file with a \"strings\" tool.",
            "How to recognise Base64: letters, digits, <code>+</code> and <code>/</code>, sometimes ending in <code>=</code>.",
        ],
        "steps": [
            ("In CyberChef, load <code>dark_photo.png</code> into Input again. This time use the <b>Strings</b> operation and set "
             "<i>Minimum length</i> to 20. Strings shows every piece of readable text in the file. You get two lines: the camera "
             "software, and the photographer's comment, which is a long string of letters and numbers.", "darkroom-2-1.png"),
            ("That string is Base64. Copy it, clear the Input box (bin icon) and paste the string in. Replace Strings in the recipe "
             "with <b>From Base64</b>.", "darkroom-2-2.png"),
            ("The decoded text has the flag and says there's another file hidden inside the photo. That's phase 3.", None),
        ],
    },
    "darkroom-3": {
        "learn": [
            "One file can hide another inside it. A PNG is made of chunks, and programs skip chunks they don't recognise.",
            "File carving: finding hidden files by looking for their signatures. Every ZIP file starts with the letters <code>PK</code>.",
            "Opening a ZIP and reading what's inside, all in the browser.",
        ],
        "steps": [
            ("In CyberChef, load <code>dark_photo.png</code> into Input and use the <b>Extract Files</b> operation. It scans the "
             "file for known file signatures. It finds the photo itself, its compressed pixel data, and a small <b>.zip</b> file "
             "that shouldn't be there.", "darkroom-3-1.png"),
            ("Click the <b>Move to input</b> button (the arrow-out-of-a-box icon) on the .zip line. The zip opens as a new Input tab. "
             "Swap the recipe for the <b>Unzip</b> operation. It shows one file, <code>last_secret.txt</code>. Click its name to "
             "see what's inside.", "darkroom-3-2.png"),
            ("<code>last_secret.txt</code> contains the last flag of the mission.", None),
        ],
    },
    "snake-1": {
        "learn": [
            "How to run a Python script from a terminal.",
            "Reading code to find out what controls its behaviour.",
            "A secret that runs on your own machine isn't protected. You can always change the code.",
        ],
        "steps": [
            ("Open the challenge and download <code>snake_stage1.py</code>.", "snake-1-1.png"),
            ("Open a terminal in the folder you saved it to. In File Explorer you can click the address bar, type "
             "<code>powershell</code> and press Enter. Run <code>python snake_stage1.py</code>. It says access denied.", "snake-1-2.png"),
            ("Open the file in a text editor (Notepad, VS Code, IDLE). Line 4 says <code>DEBUG = False</code>, and the bottom of the "
             "file only prints the secret when DEBUG is true. Change it to <code>True</code> and save.", "snake-1-3.png"),
            ("Run it again. You get the flag and a note that stage 2 needs a 4 digit PIN.", "snake-1-4.png"),
        ],
    },
    "snake-2": {
        "learn": [
            "Brute force means trying every possible answer. A 4 digit PIN only has 10,000 options, which a computer gets through in under a second.",
            "Writing a <code>for</code> loop and formatting numbers with leading zeros (<code>f\"{i:04d}\"</code>).",
            "An attempt limit only works if it's enforced somewhere you can't change it, like on a server.",
        ],
        "steps": [
            ("Download <code>snake_stage2.py</code> and read it. <code>unlock(pin)</code> hashes the PIN and compares it to "
             "<code>PIN_HASH</code>. It returns <code>None</code> when the PIN is wrong. The \"3 tries\" rule only lives in the block "
             "at the bottom.", "snake-2-1.png"),
            ("Replace that bottom block with a loop that tries every PIN from 0000 to 9999 and stops at the first one that works.",
             "snake-2-2.png"),
            ("Run it. It finishes almost instantly and prints the PIN and the flag. Write the PIN down, stage 3 needs it.",
             "snake-2-3.png"),
        ],
    },
    "snake-3": {
        "learn": [
            "Decoding Base64 in Python, and repeating it in a loop.",
            "XOR with a repeating key. XOR undoes itself: doing it twice with the same key gives back the original.",
            "When something was encoded in several steps, you undo the steps in reverse order.",
        ],
        "steps": [
            ("Download <code>snake_stage3.txt</code> and look at it. The header explains how it was made: XOR with the PIN first, "
             "then Base64 20 times. The data is the last line.", "snake-3-1.png"),
            ("Undo it backwards: Base64-decode 20 times, then XOR with the PIN. Save this as <code>solve3.py</code> in the same "
             "folder, with your PIN from stage 2:", "snake-3-2.png"),
            ("Run <code>python solve3.py</code>.", "snake-3-3.png"),
        ],
    },
    "ghost-1": {
        "learn": [
            "The Caesar cipher: every letter is shifted the same number of places in the alphabet.",
            "Why a tiny key space is weak. There are only 25 possible shifts, so you can try them all.",
            "Using CyberChef to decode things.",
        ],
        "steps": [
            ("Open transmission 1. It's gibberish, but spaces and punctuation are where you'd expect, and there's a word followed by "
             "<code>{...}</code>. That's almost certainly <code>flag{...}</code>, so the letters are shifted but nothing else is.",
             "ghost-1-1.png"),
            ("The word before the brace is <code>qwlr</code> and should be <code>flag</code>. <code>f</code> to <code>q</code> is "
             "11 letters forward, so to decode you shift 11 back, which is the same as 15 forward. Open "
             "<a href=\"https://gchq.github.io/CyberChef/\" target=\"_blank\" rel=\"noopener\">CyberChef</a>, drag in "
             "<b>ROT13</b>, set Amount to 15 and paste the text. If you don't want to work it out, just change the amount until "
             "the output makes sense.", "ghost-1-2.png"),
            ("The message has the flag and tells you the keyword for the next transmission: <code>phantom</code>.", None),
        ],
    },
    "ghost-2": {
        "learn": [
            "The Vigenère cipher: like Caesar, but the shift changes for every letter, following a keyword.",
            "It's much harder to brute force than Caesar, but easy once you know the keyword.",
        ],
        "steps": [
            ("Open transmission 2. The shift isn't the same for every letter any more, so ROT13 won't work.", "ghost-2-1.png"),
            ("In CyberChef use <b>Vigenère Decode</b> with the key <code>phantom</code> from transmission 1.", "ghost-2-2.png"),
            ("The output has the flag and says the last transmission is XOR encrypted with the key <code>spectre</code> and "
             "written as hex.", None),
        ],
    },
    "ghost-3": {
        "learn": [
            "Hex: writing bytes as pairs of characters from 0-9 and a-f.",
            "XOR with a repeating key, and that XORing again with the same key reverses it.",
            "Chaining several operations together in CyberChef.",
        ],
        "steps": [
            ("Open transmission 3. It only uses 0-9 and a-f, so it's hex.", "ghost-3-1.png"),
            ("In CyberChef add <b>From Hex</b>, then <b>XOR</b> with the key <code>spectre</code> and the key format set to UTF8.",
             "ghost-3-2.png"),
            ("The output is the last message and the final flag of the mission.", None),
        ],
    },
}
