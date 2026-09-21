from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    redirect,
    session
)

from PIL import Image, ImageDraw, ImageFont

import os
import config
import datetime
import json

app = Flask(__name__)
app.secret_key = os.getenv(
    "SECRET_KEY",
    "fallback-secret"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "fallback-password"
)

os.makedirs(config.OUTPUT_DIR, exist_ok=True)

# =========================
# COLORS
# =========================

CLIENT_RED = (180, 50, 50)
PRICE_RED = (220, 40, 40)
BLACK = (55, 55, 55)

# =========================
# FONT
# =========================

font = ImageFont.truetype(
    config.FONT_PATH,
    config.FONT_SIZE
)

# =========================
# HELPERS
# =========================

def load_requests():

    try:
        with open("requests.json", "r") as f:
            return json.load(f)

    except:
        return []


def save_requests(data):

    with open("requests.json", "w") as f:
        json.dump(data, f, indent=2)


def logged_in():

    return session.get("logged_in", False)


def draw_blended_text(draw, x, y, text, color):

    draw.text(
        (x + 2, y + 2),
        text,
        font=font,
        fill=config.SHADOW_DARK
    )

    draw.text(
        (x + 1, y + 1),
        text,
        font=font,
        fill=config.SHADOW_LIGHT
    )

    draw.text(
        (x, y),
        text,
        font=font,
        fill=color
    )


def draw_on_baseline(draw, x, line_y, text, color):

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    h = bbox[3] - bbox[1]

    y = line_y - h + config.BASELINE_OFFSET

    draw_blended_text(
        draw,
        x,
        y,
        text,
        color
    )


def generate_confirmation(
    client,
    date_input,
    time_input,
    price
):

    date = datetime.datetime.strptime(
        date_input,
        "%Y-%m-%d"
    ).strftime("%m/%d/%y")

    if time_input:

        time_val = datetime.datetime.strptime(
            time_input,
            "%H:%M"
        ).strftime("%I:%M %p").lstrip("0")

    else:

        time_val = ""

    img = Image.open(
        config.BASE_IMAGE
    ).convert("RGB")

    draw = ImageDraw.Draw(img)

    x = config.TEXT_START_X

    draw_on_baseline(
        draw,
        x,
        config.LINE_Y["client"],
        client,
        CLIENT_RED
    )

    draw_on_baseline(
        draw,
        x,
        config.LINE_Y["date"],
        date,
        BLACK
    )

    draw_on_baseline(
        draw,
        x,
        config.LINE_Y["time"],
        time_val,
        BLACK
    )

    draw_on_baseline(
        draw,
        x,
        config.LINE_Y["price"],
        f"${price}",
        PRICE_RED
    )

    filename = (
        f"{client}_"
        f"{datetime.datetime.now().strftime('%H%M%S')}.png"
    )

    img.save(
        os.path.join(
            config.OUTPUT_DIR,
            filename
        )
    )

    return filename

# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        password = request.form["password"]

        if password == ADMIN_PASSWORD:

            session["logged_in"] = True

            return redirect("/admin")

        error = "Invalid password"

    return render_template(
    "login.html",
    error=error
)

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# =========================
# PUBLIC REQUEST PAGE
# =========================
@app.route("/", methods=["GET", "POST"])
def request_form():

    if request.method == "POST":

        data = {
            "id": str(datetime.datetime.now().timestamp()),
            "client": request.form["client"],
            "phone": request.form.get("phone", ""),
            "date": request.form["date"],
            "time": request.form.get("time", ""),
            "suggested_price": request.form.get(
                "suggested_price",
                ""
            ),
            "status": "pending"
        }

        requests_data = load_requests()

        requests_data.append(data)

        save_requests(requests_data)

        return render_template(
            "success.html"
        )

    return render_template("request.html")
# =========================
# MANUAL GENERATOR
# =========================

@app.route("/generate", methods=["GET", "POST"])
def generate():

    if not logged_in():
        return redirect("/login")

    image = None

    if request.method == "POST":

        filename = generate_confirmation(
            request.form["client"],
            request.form["date"],
            request.form["time"],
            request.form["price"]
        )

        image = filename

    return render_template(
        "index.html",
        image=image
    )

# =========================
# ADMIN
# =========================
@app.route("/admin")
def admin():

    if not logged_in():
        return redirect("/login")

    requests_data = load_requests()

    for r in requests_data:

        try:

            r["display_date"] = (
                datetime.datetime.strptime(
                    r["date"],
                    "%Y-%m-%d"
                )
                .strftime("%m/%d/%Y")
            )

        except:

            r["display_date"] = r["date"]

    pending = [
        r for r in requests_data
        if r["status"] == "pending"
    ]

    for r in pending:

        try:

            r["display_time"] = (
                datetime.datetime.strptime(
                    r["time"],
                    "%H:%M"
                )
                .strftime("%I:%M %p")
                .lstrip("0")
            )

        except:

            r["display_time"] = r["time"]

    approved = [
        r for r in requests_data
        if r["status"] == "approved"
    ]

    for r in approved:

        try:

            r["display_time"] = (
                datetime.datetime.strptime(
                    r["time"],
                    "%H:%M"
                )
                .strftime("%I:%M %p")
                .lstrip("0")
            )

        except:

            r["display_time"] = r["time"]

    return render_template(
        "admin.html",
        requests=pending,
        approved=approved,
        pending_count=len(pending),
        approved_count=len(approved)
    )

# =========================
# APPROVE
# =========================

@app.route("/approve", methods=["POST"])
def approve():

    if not logged_in():
        return redirect("/login")

    req_id = request.form["id"]

    requests_data = load_requests()

    for r in requests_data:

        if r["id"] == req_id:

            client = request.form["client"]

            date_input = request.form["new_date"]

            time_input = request.form["new_time"]

            price = request.form["price"]

            filename = generate_confirmation(
                client,
                date_input,
                time_input,
                price
            )

            r["client"] = client
            r["date"] = date_input
            r["time"] = time_input
            r["approved_price"] = price
            r["approved_on"] = datetime.datetime.now().strftime(
                "%m/%d/%Y %I:%M %p"
            )
            r["status"] = "approved"
            r["file"] = filename

            break

    save_requests(requests_data)

    return redirect("/admin")

# =========================
# DELETE
# =========================

@app.route("/delete", methods=["POST"])
def delete():

    if not logged_in():
        return redirect("/login")

    req_id = request.form["id"]

    requests_data = load_requests()

    for r in requests_data:

        if r["id"] == req_id:

            r["status"] = "deleted"

    save_requests(requests_data)

    return redirect("/admin")

# =========================
# IMAGE ACCESS
# =========================

@app.route("/output/<filename>")
def serve_image(filename):

    if not logged_in():
        return redirect("/login")

    return send_from_directory(
        config.OUTPUT_DIR,
        filename
    )

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run()
