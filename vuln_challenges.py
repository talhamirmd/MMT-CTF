import base64

from flask import Blueprint, abort, make_response, render_template, request

from challenges import FLAGS, GHOST_TEXT_1, GHOST_TEXT_2, GHOST_TEXT_3, NOVA_ACCESS_CODE, SNAKE_LAYERS

bp = Blueprint("chal", __name__)


NOVA_COOKIE_PATH = "/chal/m/nova"


@bp.route("/chal/m/nova")
def nova_home():
    message = (f"employee of the month: {FLAGS['nova-1']} "
               f"(staff portal moved to /chal/m/nova/staff)")
    return render_template("chal/nova_home.html", codes=[ord(c) ^ 7 for c in message])


@bp.route("/chal/m/nova/staff", methods=["GET", "POST"])
def nova_staff():
    clearance = request.cookies.get("clearance")
    error = None
    if request.method == "POST":
        if request.form.get("code", "").strip() == NOVA_ACCESS_CODE:
            clearance = "staff"
        else:
            error = "Wrong access code."
    resp = make_response(render_template(
        "chal/nova_staff.html", error=error, logged_in=clearance in ("staff", "admin"),
        flag=FLAGS["nova-2"], code_b64=base64.b64encode(NOVA_ACCESS_CODE.encode()).decode()))
    if request.method == "POST" and not error:
        resp.set_cookie("clearance", "staff", path=NOVA_COOKIE_PATH, samesite="Lax")
    return resp


@bp.route("/chal/m/nova/vault")
def nova_vault():
    clearance = request.cookies.get("clearance")
    return render_template("chal/nova_vault.html", clearance=clearance,
                           flag=FLAGS["nova-3"] if clearance == "admin" else None)


@bp.route("/chal/m/darkroom")
def darkroom():
    return render_template("chal/darkroom.html")


SNAKE_STAGES = {
    1: ("Debug mode", "snake_stage1.py", "This script has the flag but won't print it."),
    2: ("PIN", "snake_stage2.py", "Needs a 4 digit PIN. You get 3 tries."),
    3: ("Layers", "snake_stage3.txt", f"XOR with the PIN, then base64 {SNAKE_LAYERS} times."),
}


@bp.route("/chal/m/snake/<int:stage>")
def snake(stage):
    if stage not in SNAKE_STAGES:
        abort(404)
    name, filename, blurb = SNAKE_STAGES[stage]
    return render_template("chal/snake.html", stage=stage, name=name, filename=filename, blurb=blurb,
                           stages=SNAKE_STAGES)


GHOST_TRANSMISSIONS = {
    1: ("Caesar", GHOST_TEXT_1),
    2: ("Vigenère", GHOST_TEXT_2),
    3: ("XOR / hex", GHOST_TEXT_3),
}


@bp.route("/chal/m/ghost/<int:n>")
def ghost(n):
    if n not in GHOST_TRANSMISSIONS:
        abort(404)
    return render_template("chal/ghost.html", n=n, text=GHOST_TRANSMISSIONS[n][1], total=len(GHOST_TRANSMISSIONS))
