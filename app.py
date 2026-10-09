import argparse
import getpass
import hmac
import os
import re
import secrets
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import db as database
import generate_files
from challenges import CHALLENGES, CHALLENGES_BY_ID, FLAG_FORMAT, MISSIONS, MISSIONS_BY_ID
from guides import GUIDES
from vuln_challenges import bp as vuln_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

CTF_NAME = os.environ.get("CTF_NAME", "MMT_CTF")
DB_PATH = os.environ.get("CTF_DB", os.path.join(INSTANCE_DIR, "ctf.db"))
SUBMISSION_LIMIT = 10      # attempts allowed...
SUBMISSION_WINDOW = 60     # ...per this many seconds, per player
TRUST_PROXY = os.environ.get("TRUST_PROXY") == "1"
GUIDE_DELAY = 15 * 60      # seconds on a phase before its guide unlocks
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")
MIN_PASSWORD = 8


def _parse_time(value):
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


CTF_START = _parse_time(os.environ.get("CTF_START"))
CTF_END = _parse_time(os.environ.get("CTF_END"))


def _secret_key():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    path = os.path.join(INSTANCE_DIR, "secret_key")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(path) as f:
        return f.read().strip()


app = Flask(__name__)
app.config.update(
    SECRET_KEY=_secret_key(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=TRUST_PROXY,
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    MAX_CONTENT_LENGTH=64 * 1024,
)
app.register_blueprint(vuln_bp)
if TRUST_PROXY:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)


def get_db():
    if "db" not in g:
        g.db = database.Database(DB_PATH)
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ctf_status():
    now = time.time()
    if CTF_START and now < CTF_START:
        return "upcoming"
    if CTF_END and now > CTF_END:
        return "ended"
    return "running"


def hidden_challenge_ids():
    rows = get_db().execute("SELECT challenge_id FROM challenge_state WHERE hidden = 1").fetchall()
    return {r["challenge_id"] for r in rows}


def visible_challenges():
    hidden = hidden_challenge_ids()
    return [c for c in CHALLENGES if c["id"] not in hidden]


def solve_counts():
    rows = get_db().execute("SELECT challenge_id, COUNT(*) AS n FROM solves GROUP BY challenge_id").fetchall()
    return {r["challenge_id"]: r["n"] for r in rows}


def player_solved():
    if not g.user:
        return set()
    rows = get_db().execute("SELECT challenge_id FROM solves WHERE user_id = ?", (g.user["id"],)).fetchall()
    return {r["challenge_id"] for r in rows if r["challenge_id"] in CHALLENGES_BY_ID}


_attempts = defaultdict(deque)


def rate_limited(key):
    now, q = time.time(), _attempts[key]
    while q and now - q[0] > SUBMISSION_WINDOW:
        q.popleft()
    if len(q) >= SUBMISSION_LIMIT:
        return True
    q.append(now)
    return False


def is_locked(chal, solved):
    return bool(chal["requires"]) and chal["requires"] not in solved and not is_admin()


def start_guide_timer(cid):
    # first time this player opens the phase
    if g.user:
        get_db().execute("INSERT INTO opened (user_id, challenge_id, opened_at) VALUES (?, ?, ?) "
                         "ON CONFLICT DO NOTHING", (g.user["id"], cid, time.time()))
        get_db().commit()


def guide_state(chal, solved):
    """Returns (state, seconds_left). state is open, waiting, not_started or locked."""
    if is_admin() or chal["id"] in solved:
        return "open", 0
    if is_locked(chal, solved):
        return "locked", None
    row = None
    if g.user:
        row = get_db().execute("SELECT opened_at FROM opened WHERE user_id = ? AND challenge_id = ?",
                               (g.user["id"], chal["id"])).fetchone()
    if row is None:
        return "not_started", None
    left = int(row["opened_at"] + GUIDE_DELAY - time.time())
    return ("open", 0) if left <= 0 else ("waiting", left)


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def is_admin():
    return g.get("admin") is not None


@app.before_request
def load_accounts():
    g.admin = g.user = None
    if session.get("admin_id") is not None:
        g.admin = get_db().execute("SELECT * FROM admins WHERE id = ?", (session["admin_id"],)).fetchone()
        if g.admin is None:
            session.pop("admin_id", None)
    if session.get("user_id") is not None:
        g.user = get_db().execute("SELECT id, username FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        if g.user is None:
            session.pop("user_id", None)


@app.before_request
def csrf_protect():
    # challenge pages have their own forms
    if request.method == "POST" and request.blueprint != vuln_bp.name:
        token = session.get("csrf_token")
        if not token or not hmac.compare_digest(token, request.form.get("csrf_token", "")):
            abort(400, "Invalid or missing CSRF token. Reload the page and try again.")


@app.context_processor
def inject_globals():
    return {
        "ctf_name": CTF_NAME,
        "csrf_token": csrf_token,
        "admin": g.get("admin"),
        "user": g.get("user"),
        "ctf_status": ctf_status(),
        "ctf_start": CTF_START,
        "ctf_end": CTF_END,
        "flag_format": FLAG_FORMAT,
    }


@app.template_filter("dt")
def format_ts(ts):
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_admin():
            abort(404)
        return view(*args, **kwargs)
    return wrapped


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user and not is_admin():
            flash("Log in or make an account to play.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def safe_next(default="challenges"):
    nxt = request.args.get("next", "")
    # only allow paths on this site
    return nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for(default)


def log_in(user_id):
    session.clear()
    session["user_id"] = user_id
    session.permanent = True


@app.route("/")
def index():
    phases = visible_challenges()
    stats = {"missions": len({c["mission"] for c in phases}), "phases": len(phases),
             "players": get_db().execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]}
    return render_template("index.html", stats=stats)


@app.route("/rules")
def rules():
    return render_template("rules.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("challenges"))
    username = request.form.get("username", "").strip()
    if request.method == "POST":
        password = request.form.get("password", "")
        db = get_db()
        if rate_limited("register:" + (request.remote_addr or "?")):
            flash("Too many attempts. Wait a minute.", "error")
        elif not USERNAME_RE.match(username):
            flash("Usernames are 3 to 24 characters: letters, numbers, _ . and -", "error")
        elif len(password) < MIN_PASSWORD:
            flash(f"Your password needs at least {MIN_PASSWORD} characters.", "error")
        elif password != request.form.get("confirm", ""):
            flash("The passwords don't match.", "error")
        elif db.execute("SELECT 1 FROM users WHERE lower(username) = lower(?)", (username,)).fetchone():
            flash("That username is taken.", "error")
        else:
            row = db.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?) RETURNING id",
                             (username, generate_password_hash(password), time.time())).fetchone()
            db.commit()
            log_in(row["id"])
            flash(f"Welcome, {username}! Your progress is saved to your account.", "success")
            return redirect(safe_next())
    return render_template("register.html", username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("challenges"))
    username = request.form.get("username", "").strip()
    if request.method == "POST":
        if rate_limited("login:" + (request.remote_addr or "?")):
            flash("Too many attempts. Wait a minute.", "error")
        else:
            row = get_db().execute("SELECT id, username, password_hash FROM users WHERE lower(username) = lower(?)",
                                   (username,)).fetchone()
            if row and check_password_hash(row["password_hash"], request.form.get("password", "")):
                log_in(row["id"])
                flash(f"Welcome back, {row['username']}.", "success")
                return redirect(safe_next())
            flash("Wrong username or password.", "error")
    return render_template("login.html", username=username)


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    flash("Logged out.", "info")
    return redirect(url_for("index"))


@app.route("/scoreboard")
def scoreboard():
    rows = get_db().execute(
        "SELECT u.id, u.username, s.challenge_id, s.created_at FROM users u JOIN solves s ON s.user_id = u.id"
    ).fetchall()
    players = {}
    for r in rows:
        chal = CHALLENGES_BY_ID.get(r["challenge_id"])
        if chal is None:
            continue
        p = players.setdefault(r["id"], {"id": r["id"], "username": r["username"], "score": 0, "solves": 0, "last": 0})
        p["score"] += chal["points"]
        p["solves"] += 1
        p["last"] = max(p["last"], r["created_at"])
    # higher score first; on a tie, whoever got there first
    board = sorted(players.values(), key=lambda p: (-p["score"], p["last"]))
    return render_template("scoreboard.html", board=board, total=sum(c["points"] for c in CHALLENGES))


@app.route("/challenges")
@login_required
def challenges():
    if ctf_status() == "upcoming" and not is_admin():
        return render_template("not_started.html")
    chals = CHALLENGES if is_admin() else visible_challenges()
    solved = player_solved()
    visible_ids = {c["id"] for c in chals}
    missions = [(m, [p for p in m["phases"] if p["id"] in visible_ids]) for m in MISSIONS]
    missions = [(m, ps) for m, ps in missions if ps]
    score = sum(CHALLENGES_BY_ID[cid]["points"] for cid in solved)
    return render_template("challenges.html", missions=missions, solved=solved, score=score,
                           total=sum(c["points"] for c in chals))


@app.route("/challenge/<cid>", methods=["GET", "POST"])
@login_required
def challenge(cid):
    chal = visible_or_404(cid)
    db = get_db()
    player_solves = player_solved()
    solved = cid in player_solves
    locked = is_locked(chal, player_solves)

    if request.method == "POST":
        if not g.user:
            flash("Log in as a player to submit flags.", "error")
        elif locked:
            flash("Solve the previous phase first.", "error")
        elif ctf_status() == "ended" and not is_admin():
            flash("The CTF is over, submissions are closed.", "error")
        elif solved:
            flash("You already solved this one.", "info")
        elif rate_limited(f"user:{g.user['id']}") or rate_limited(request.remote_addr or "?"):
            flash(f"Too many tries. You get {SUBMISSION_LIMIT} per minute.", "error")
        else:
            submitted = request.form.get("flag", "").strip()[:200]
            correct = hmac.compare_digest(submitted.encode(), chal["flag"].encode())
            now = time.time()
            db.execute("INSERT INTO submissions (user_id, challenge_id, submitted, correct, created_at) "
                       "VALUES (?, ?, ?, ?, ?)", (g.user["id"], cid, submitted, int(correct), now))
            if correct:
                db.execute("INSERT INTO solves (user_id, challenge_id, created_at) VALUES (?, ?, ?) "
                           "ON CONFLICT DO NOTHING", (g.user["id"], cid, now))
                unlocked = f" Phase {chal['phase'] + 1} is unlocked." if chal["next"] else ""
                flash(f"Correct, +{chal['points']} points.{unlocked}", "success")
            elif not submitted.startswith("flag{"):
                flash("Wrong. Flags look like flag{...}", "error")
            else:
                flash("Wrong flag.", "error")
            db.commit()
        return redirect(url_for("challenge", cid=cid))

    if not locked:
        start_guide_timer(cid)
    return render_template("challenge.html", chal=chal, solved=solved, locked=locked,
                           mission=MISSIONS_BY_ID.get(chal["mission"]), player_solves=player_solves,
                           solve_count=solve_counts().get(cid, 0), guide=guide_state(chal, player_solves))


def visible_or_404(cid):
    chal = CHALLENGES_BY_ID.get(cid)
    if chal is None or (not is_admin() and (cid in hidden_challenge_ids() or ctf_status() == "upcoming")):
        abort(404)
    return chal


@app.route("/guide")
@login_required
def guide_index():
    if ctf_status() == "upcoming" and not is_admin():
        return render_template("not_started.html")
    solved = player_solved()
    hidden = set() if is_admin() else hidden_challenge_ids()
    missions = [(m, [(p, guide_state(p, solved)) for p in m["phases"] if p["id"] not in hidden]) for m in MISSIONS]
    return render_template("guide_index.html", missions=[(m, ps) for m, ps in missions if ps],
                           delay_min=GUIDE_DELAY // 60)


@app.route("/guide/<cid>")
@login_required
def guide(cid):
    chal = visible_or_404(cid)
    state, left = guide_state(chal, player_solved())
    return render_template("guide.html", chal=chal, mission=MISSIONS_BY_ID[chal["mission"]], state=state, left=left,
                           guide=GUIDES.get(cid), delay_min=GUIDE_DELAY // 60)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if is_admin():
        return redirect(url_for("admin"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if rate_limited("admin-login:" + (request.remote_addr or "?")):
            flash("Too many attempts. Wait a minute.", "error")
        else:
            row = get_db().execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
            if row and check_password_hash(row["password_hash"], password):
                session["admin_id"] = row["id"]
                return redirect(url_for("admin"))
            flash("Invalid username or password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_id", None)
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    submissions = db.execute(
        "SELECT s.*, u.username FROM submissions s LEFT JOIN users u ON u.id = s.user_id "
        "ORDER BY s.created_at DESC LIMIT 100").fetchall()
    totals = db.execute("SELECT COUNT(*) AS total, COALESCE(SUM(correct), 0) AS correct FROM submissions").fetchone()
    players = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    return render_template("admin.html", submissions=submissions, challenges=CHALLENGES,
                           counts=solve_counts(), hidden=hidden_challenge_ids(),
                           total_submissions=totals["total"], correct_submissions=totals["correct"], players=players,
                           chal_names={c["id"]: c["name"] for c in CHALLENGES})


@app.route("/admin/challenge/<cid>/toggle", methods=["POST"])
@admin_required
def admin_toggle_challenge(cid):
    if cid not in CHALLENGES_BY_ID:
        abort(404)
    db = get_db()
    hidden = 0 if cid in hidden_challenge_ids() else 1
    db.execute("INSERT INTO challenge_state (challenge_id, hidden) VALUES (?, ?) "
               "ON CONFLICT(challenge_id) DO UPDATE SET hidden = excluded.hidden", (cid, hidden))
    db.commit()
    flash(f"Challenge '{CHALLENGES_BY_ID[cid]['name']}' is now {'hidden' if hidden else 'visible'}.", "info")
    return redirect(url_for("admin"))


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, message=e.description), 400


def save_admin(username, password):
    if not USERNAME_RE.match(username):
        sys.exit("Invalid admin username (3-24 chars: letters, numbers, _ . -).")
    if len(password) < MIN_PASSWORD:
        sys.exit(f"Admin password must be at least {MIN_PASSWORD} characters.")
    db = database.Database(DB_PATH)
    db.execute("INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, ?) "
               "ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash",
               (username, generate_password_hash(password), time.time()))
    db.commit()
    db.close()


database.init(DB_PATH)
generate_files.generate()
if os.environ.get("ADMIN_USERNAME") and os.environ.get("ADMIN_PASSWORD"):
    save_admin(os.environ["ADMIN_USERNAME"], os.environ["ADMIN_PASSWORD"])


def create_admin(username):
    password = getpass.getpass("Admin password: ")
    if password != getpass.getpass("Confirm password: "):
        sys.exit("Passwords don't match.")
    save_admin(username, password)
    print(f"Admin '{username}' saved. Log in at /admin/login")


def main():
    parser = argparse.ArgumentParser(description=f"{CTF_NAME} platform")
    sub = parser.add_subparsers(dest="command")
    run_p = sub.add_parser("run", help="run the development server (default)")
    run_p.add_argument("--host", default="127.0.0.1")
    run_p.add_argument("--port", type=int, default=5000)
    run_p.add_argument("--debug", action="store_true")
    admin_p = sub.add_parser("create-admin", help="create an admin account or reset its password")
    admin_p.add_argument("username")
    sub.add_parser("generate-files", help="rebuild static/files from the flags")
    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin(args.username)
    elif args.command == "generate-files":
        print("Generated:", ", ".join(generate_files.generate(force=True)))
    else:
        app.run(host=getattr(args, "host", "127.0.0.1"), port=getattr(args, "port", 5000),
                debug=getattr(args, "debug", False))


if __name__ == "__main__":
    main()
