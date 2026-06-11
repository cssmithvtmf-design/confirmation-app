from flask import Flask, render_template, request, send_from_directory, redirect
from PIL import Image, ImageDraw, ImageFont
import os
import config
import datetime
import json

app = Flask(__name__)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)
# =========================
# COLORS
# =========================
CLIENT_RED = (180, 50, 50)
PRICE_RED  = (220, 40, 40)
BLACK      = (55, 55, 55)

# =========================
# FONT
# =========================
font = ImageFont.truetype(config.FONT_PATH, config.FONT_SIZE)


# =========================
# DRAW FUNCTIONS
# =========================
def draw_blended_text(draw, x, y, text, color):
    draw.text((x+2, y+2), text, font=font, fill=config.SHADOW_DARK)
    draw.text((x+1, y+1), text, font=font, fill=config.SHADOW_LIGHT)
    draw.text((x, y), text, font=font, fill=color)

def draw_on_baseline(draw, x, line_y, text, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    h = bbox[3] - bbox[1]
    y = line_y - h + config.BASELINE_OFFSET
    draw_blended_text(draw, x, y, text, color)


# =========================
# SERVE IMAGE
# =========================
@app.route("/output/<filename>")
def serve_image(filename):
    #return send_from_directory(config.OUTPUT_DIR, filename)
    return send_from_directory(config.OUTPUT_DIR, filename, as_attachment=True)


# =========================
# MAIN GENERATOR PAGE
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    image = None

    if request.method == "POST":
        client = request.form["client"]

        # DATE FORMAT
        date_input = request.form["date"]
        try:
            d = datetime.datetime.strptime(date_input, "%Y-%m-%d")
            date = d.strftime("%m/%d/%y")
        except:
            date = date_input

        # TIME FORMAT
        time_input = request.form["time"]
        try:
            t = datetime.datetime.strptime(time_input, "%H:%M")
            time_val = t.strftime("%I:%M %p").lstrip("0")
        except:
            time_val = time_input

        price = request.form["price"]

        img = Image.open(config.BASE_IMAGE).convert("RGB")
        draw = ImageDraw.Draw(img)

        x = config.TEXT_START_X

        draw_on_baseline(draw, x, config.LINE_Y["client"], client, CLIENT_RED)
        draw_on_baseline(draw, x, config.LINE_Y["date"], date, BLACK)
        draw_on_baseline(draw, x, config.LINE_Y["time"], time_val, BLACK)
        draw_on_baseline(draw, x, config.LINE_Y["price"], f"{price}", PRICE_RED)

        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        filename = f"{client}_{datetime.datetime.now().strftime('%H%M%S')}.png"
        img.save(os.path.join(config.OUTPUT_DIR, filename))

        image = filename

    return render_template("index.html", image=image)


# =========================
# CLIENT REQUEST
# =========================
@app.route("/request", methods=["GET", "POST"])
def request_form():

    if request.method == "POST":
        data = {
            "id": str(datetime.datetime.now().timestamp()),
            "client": request.form["client"],
            "date": request.form["date"],
            "time": request.form.get("time", ""),
            "status": "pending"
        }

        try:
            with open("requests.json") as f:
                requests = json.load(f)
        except:
            requests = []

        requests.append(data)

        with open("requests.json", "w") as f:
            json.dump(requests, f, indent=2)

        return "<h3>✅ Request Submitted</h3>"

    return render_template("request.html")


# =========================
# ADMIN PANEL
# =========================
@app.route("/admin")
def admin():
    try:
        with open("requests.json") as f:
            requests = json.load(f)
    except:
        requests = []

    pending = [r for r in requests if r["status"] == "pending"]

    return render_template("admin.html", requests=pending)


# =========================
# APPROVE
# =========================
@app.route("/approve", methods=["POST"])
def approve():

    req_id = request.form["id"]

    with open("requests.json") as f:
        requests = json.load(f)

    for r in requests:
        if r["id"] == req_id:
            r["status"] = "approved"

            client = r["client"]
            date_input = r["date"]
            time_input = request.form["new_time"]
            price = request.form["price"]

            # format
            date = datetime.datetime.strptime(date_input, "%Y-%m-%d").strftime("%m/%d/%y")
            time_val = datetime.datetime.strptime(time_input, "%H:%M").strftime("%I:%M %p").lstrip("0")

            img = Image.open(config.BASE_IMAGE).convert("RGB")
            draw = ImageDraw.Draw(img)

            x = config.TEXT_START_X

            draw_on_baseline(draw, x, config.LINE_Y["client"], client, CLIENT_RED)
            draw_on_baseline(draw, x, config.LINE_Y["date"], date, BLACK)
            draw_on_baseline(draw, x, config.LINE_Y["time"], time_val, BLACK)
            draw_on_baseline(draw, x, config.LINE_Y["price"], f"${price}", PRICE_RED)

            filename = f"{client}_{datetime.datetime.now().strftime('%H%M%S')}.png"
            img.save(os.path.join(config.OUTPUT_DIR, filename))

            r["file"] = filename
            break

    with open("requests.json", "w") as f:
        json.dump(requests, f, indent=2)

    return redirect("/admin")


# =========================
# DELETE
# =========================
@app.route("/delete", methods=["POST"])
def delete():

    req_id = request.form["id"]

    with open("requests.json") as f:
        requests = json.load(f)

    for r in requests:
        if r["id"] == req_id:
            r["status"] = "deleted"

    with open("requests.json", "w") as f:
        json.dump(requests, f, indent=2)

    return redirect("/admin")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run()
