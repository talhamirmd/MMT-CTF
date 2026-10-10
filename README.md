# MMT_CTF

A small CTF site made with Flask. It has 4 missions and each mission has 3 phases. You need the flag from one phase to unlock the next one.

| Mission | Category | What you do |
|---|---|---|
| Operation NovaTech | Web | inspect element, browser console, cookies |
| The Dark Room | Forensics | image brightness, metadata, hidden zip |
| Snake Lab | Python | edit a script, brute force a PIN, decode base64 + xor |
| Ghost Signal | Crypto | caesar, vigenere, xor |

Players sign up with a username and password. Their solves, score and guide timers are saved to their account, so they can log out and carry on later from any device. The Scoreboard page ranks everyone by points (ties go to whoever got there first).

Each phase has 3 hints and a step by step guide with screenshots (the Guide page). A phase's guide unlocks after the player has spent 15 minutes on it, or once they solve it. The screenshots in `static/guide/` show `flag{...}` instead of real flags; the real flag is only added to the page when the guide unlocks.


**LIVE LINK - https://mmt-ctf.onrender.com/**

## Running it locally

1. Copy `flags.example.json` to `flags.json` and put your own flags in it. Flags can use lowercase letters, numbers, `_ { } : .` and spaces.
2. Install the requirements and start the site:
   ```
   python -m venv .venv
   .venv\Scripts\activate        (Linux/Mac: source .venv/bin/activate)
   pip install -r requirements.txt
   python app.py
   ```
3. Open http://127.0.0.1:5000. Next time you only need to activate the venv and run `python app.py`.

Locally, accounts and scores are stored in `instance/ctf.db` (SQLite).

To make an admin account run `python app.py create-admin <name>`. The admin page is at `/admin/login`.

## Deploying on Render

1. Push the repo to GitHub. `flags.json` is in `.gitignore` so it won't be uploaded.
2. On Render go to New > Blueprint and select the repo. It uses `render.yaml`.
3. Make a free Postgres database for the accounts and scores. [Neon](https://neon.tech) works well and its free plan doesn't expire: create a project and copy its connection string (it starts with `postgresql://`).
4. Fill in `CTF_FLAGS` (paste the contents of flags.json), `DATABASE_URL` (the connection string), `ADMIN_USERNAME` and `ADMIN_PASSWORD`.

You need the database because Render's free plan wipes its disk every time the site restarts or wakes up from sleep. Without `DATABASE_URL` every account would disappear, and the logs will show a warning. Render has its own free Postgres too, but it's deleted after 30 days.

## Settings

These can be set as environment variables:

- `CTF_NAME` - site name (default MMT_CTF)
- `CTF_START` / `CTF_END` - start and end time, e.g. `2026-11-01T18:00`
- `CTF_FLAGS` - flags as JSON instead of flags.json
- `DATABASE_URL` - Postgres connection string for accounts and scores (without it, SQLite in `instance/` is used)
- `SECRET_KEY` - session key
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` - creates the admin account on startup
- `TRUST_PROXY` - set to 1 when running behind Render or another https proxy
