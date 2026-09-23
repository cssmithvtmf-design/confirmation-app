from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    redirect,
    session,
    jsonify
)

from PIL import Image, ImageDraw, ImageFont

import os
import config
import datetime
from database import (
    get_requests_as_dicts,
    insert_request,
    approve_request,
    delete_request,
    get_all_business_hours,
    get_scheduler_settings,
    update_scheduler_settings,
    update_business_hour,
    get_requests_for_date,
    return_to_pending,
    export_requests_json
)
from database import initialize_database
from schedule import (
    get_available_slots,
    get_all_slots_for_date,
    convert_display_time_to_db,
    get_available_slot_count
)
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
initialize_database()
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

            return redirect("/dashboard")

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
            "time": convert_display_time_to_db(
                request.form.get("time", "")
            ),
            "suggested_price": request.form.get(
                "suggested_price",
                ""
            ),
            "notes": request.form.get(
                "notes",
                ""
            ),
            "status": "pending"
        }

        insert_request(data)
        export_requests_json()
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
# AVAILABILITY TEST
# =========================
@app.route(
    "/admin-schedule",
    methods=["GET", "POST"]
)
def admin_schedule():

    if not logged_in():
        return redirect("/login")

    if request.method == "POST":

        appointment_minutes = int(
            request.form["appointment_minutes"]
        )

        buffer_minutes = int(
            request.form["buffer_minutes"]
        )
    if appointment_minutes < 15:
        return "Appointment length must be at least 15 minutes."
    if buffer_minutes < 0:
        return "Buffer cannot be negative."
    
        update_scheduler_settings(
            appointment_minutes,
            buffer_minutes
        )

        for row_id in range(1, 8):

            start_time = request.form.get(
                f"start_{row_id}",
                ""
            )

            end_time = request.form.get(
                f"end_{row_id}",
                ""
            )
            if active:
                if start_time >= end_time:
                    return f"Invalid hours for day {row_id}"

            active = 1 if request.form.get(
                f"active_{row_id}"
            ) else 0

            update_business_hour(
                row_id,
                start_time,
                end_time,
                active
            )

        return redirect(
            "/admin-schedule"
        )

    hours = get_all_business_hours()

    settings = get_scheduler_settings()

    return render_template(
        "schedule_admin.html",
        hours=hours,
        settings=settings
    )
@app.route("/image-maintenance")
def image_maintenance():

    if not logged_in():
        return redirect("/login")

    output_dir = "output"

    image_files = []

    if os.path.exists(output_dir):

        for file_name in os.listdir(output_dir):

            if file_name.lower().endswith(".png"):

                image_files.append(file_name)

    image_files.sort()

    return render_template(
        "image_maintenance.html",
        image_files=image_files,
        image_count=len(image_files)
    )
    
@app.route("/dashboard")
def dashboard():

    if not logged_in():
        return redirect("/login")

    requests_data = get_requests_as_dicts()

    pending_count = len([
        r for r in requests_data
        if r["status"] == "pending"
    ])

    approved_count = len([
        r for r in requests_data
        if r["status"] == "approved"
    ])

    settings = get_scheduler_settings()
    today = datetime.date.today().strftime(
        "%Y-%m-%d"
    )
    available_slots = (
        get_available_slot_count(
            today
        )
    )
    today_schedule = []
    booked = get_requests_for_date(
        today
    )
    booked_lookup = {}
    for row in booked:
        booked_lookup[row[1]] = (
            row[0],
            row[2]
        )
    for slot in get_all_slots_for_date(today):
        slot_24 = (
            convert_display_time_to_db(
                slot
            )
        )
        if slot_24 in booked_lookup:
            today_schedule.append({
                "time": slot,
                "client": booked_lookup[
                    slot_24
                ][0],
                "status": booked_lookup[
                    slot_24
                ][1]
            })
        else:
            today_schedule.append({
                "time": slot,
                "client": "Available",
                "status": "available"
            })
    return render_template(
        "dashboard.html",
        pending_count=pending_count,
        approved_count=approved_count,
        settings=settings,
        available_slots=available_slots,
        today_schedule=today_schedule
    )
@app.route("/api/availability/<date_string>")
def api_availability(date_string):

    slots = get_available_slots(
        date_string
    )

    return jsonify(slots)
# =========================
# ADMIN
# =========================
@app.route("/admin")
def admin():

    if not logged_in():
        return redirect("/login")

    requests_data = get_requests_as_dicts()
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

    approve_request(
        req_id,
        client,
        date_input,
        time_input,
        price,
        filename
    )
    export_requests_json()
    return redirect("/admin")
# =============================
# RETURN TO PENDING(UN-APPROVE)
# =============================
@app.route(
    "/return-pending",
    methods=["POST"]
)
def return_pending():

    if not logged_in():
        return redirect("/login")

    req_id = request.form["id"]

    return_to_pending(req_id)
    export_requests_json()
    return redirect("/admin")
# =========================
# DELETE
# =========================

@app.route("/delete", methods=["POST"])
def delete():

    if not logged_in():
        return redirect("/login")

    req_id = request.form["id"]

    delete_request(req_id)
    export_requests_json()
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
