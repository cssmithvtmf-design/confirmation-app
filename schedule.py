import sqlite3
import datetime


DB_NAME = "appointments.db"


def get_connection():

    return sqlite3.connect(DB_NAME)


def get_settings():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        appointment_minutes,
        buffer_minutes
    FROM settings
    WHERE id = 1
    """)

    settings = cursor.fetchone()

    conn.close()

    return {

        "appointment_minutes": settings[0],
        "buffer_minutes": settings[1]

    }


def get_business_hours(day_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        start_time,
        end_time,
        active
    FROM business_hours
    WHERE day_of_week = ?
    """, (day_name,))

    row = cursor.fetchone()

    conn.close()

    if not row:

        return None

    return {

        "start_time": row[0],
        "end_time": row[1],
        "active": row[2]

    }

def get_booked_slots(date_string):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT time
    FROM requests
    WHERE date = ?
    AND status IN ('pending','approved')
    """, (date_string,))

    rows = cursor.fetchall()

    conn.close()

    booked = []

    for row in rows:

        booked.append(row[0])

    return booked

def generate_slots(day_name):

    settings = get_settings()

    business_hours = get_business_hours(day_name)

    if not business_hours:

        return []

    if business_hours["active"] == 0:

        return []

    appointment_minutes = settings["appointment_minutes"]

    buffer_minutes = settings["buffer_minutes"]

    slot_minutes = (
        appointment_minutes
        + buffer_minutes
    )

    start_time = datetime.datetime.strptime(
        business_hours["start_time"],
        "%H:%M"
    )

    end_time = datetime.datetime.strptime(
        business_hours["end_time"],
        "%H:%M"
    )

    slots = []

    current = start_time

    while current <= end_time:

        slots.append(

            current.strftime("%I:%M %p")
            .lstrip("0")

        )

        current += datetime.timedelta(
            minutes=slot_minutes
        )

    return slots

def generate_slots_for_date(date_string):

    date_obj = datetime.datetime.strptime(
        date_string,
        "%Y-%m-%d"
    )

    day_name = date_obj.strftime("%A")

    slots = generate_slots(day_name)

    booked = get_booked_slots(
        date_string
    )

    available = []

    for slot in slots:

        slot_24 = (
            datetime.datetime.strptime(
                slot,
                "%I:%M %p"
            )
            .strftime("%H:%M")
        )

        if slot_24 not in booked:

            available.append(slot)

    return available

def get_available_slots(date_string):

    return generate_slots_for_date(
        date_string
    )

def get_all_slots_for_date(date_string):

    date_obj = datetime.datetime.strptime(
        date_string,
        "%Y-%m-%d"
    )

    day_name = date_obj.strftime("%A")

    return generate_slots(day_name)


def get_available_slot_count(date_string):

    return len(
        get_available_slots(
            date_string
        )
    )

def is_slot_available(
    date_string,
    time_string
):

    available_slots = get_available_slots(
        date_string
    )

    try:

        display_time = (
            datetime.datetime.strptime(
                time_string,
                "%H:%M"
            )
            .strftime("%I:%M %p")
            .lstrip("0")
        )

    except:

        display_time = time_string

    return display_time in available_slots
def convert_display_time_to_db(time_string):

    return (
        datetime.datetime.strptime(
            time_string,
            "%I:%M %p"
        )
        .strftime("%H:%M")
    )

if __name__ == "__main__":

    print()

    print(
        "09:00 Available:",
        is_slot_available(
            "2026-09-26",
            "09:00"
        )
    )

    print(
        "10:15 Available:",
        is_slot_available(
            "2026-09-26",
            "10:15"
        )
    )

    print(
        "12:45 Available:",
        is_slot_available(
            "2026-09-26",
            "12:45"
        )
    )

    print(
        "14:00 Available:",
        is_slot_available(
            "2026-09-26",
            "14:00"
        )
    )

    print(
        convert_display_time_to_db(
            "2:00 PM"
        )
    )