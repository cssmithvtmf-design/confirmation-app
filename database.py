import sqlite3
import datetime

DB_NAME = "appointments.db"


def get_connection():

    return sqlite3.connect(DB_NAME)


def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()

    # =====================================
    # REQUESTS TABLE
    # =====================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (

        id TEXT PRIMARY KEY,

        client TEXT,

        phone TEXT,

        notes TEXT,

        date TEXT,

        time TEXT,

        suggested_price TEXT,

        approved_price TEXT,

        approved_on TEXT,

        status TEXT,

        file TEXT

    )
    """)

    # =====================================
    # BUSINESS HOURS TABLE
    # =====================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS business_hours (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        day_of_week TEXT,

        start_time TEXT,

        end_time TEXT,

        active INTEGER

    )
    """)

    # =====================================
    # SETTINGS TABLE
    # =====================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (

        id INTEGER PRIMARY KEY,

        appointment_minutes INTEGER,

        buffer_minutes INTEGER

    )
    """)

    # =====================================
    # DEFAULT BUSINESS HOURS
    # =====================================

    cursor.execute(
        "SELECT COUNT(*) FROM business_hours"
    )

    row_count = cursor.fetchone()[0]

    if row_count == 0:

        default_hours = [

            ("Monday", "09:00", "17:00", 1),
            ("Tuesday", "09:00", "17:00", 1),
            ("Wednesday", "09:00", "17:00", 1),
            ("Thursday", "09:00", "17:00", 1),
            ("Friday", "09:00", "17:00", 1),
            ("Saturday", "09:00", "14:00", 1),
            ("Sunday", "", "", 0)

        ]

        cursor.executemany("""

        INSERT INTO business_hours (

            day_of_week,
            start_time,
            end_time,
            active

        )

        VALUES (?, ?, ?, ?)

        """, default_hours)

    # =====================================
    # DEFAULT SETTINGS
    # =====================================

    cursor.execute(
        "SELECT COUNT(*) FROM settings"
    )

    row_count = cursor.fetchone()[0]

    if row_count == 0:

        cursor.execute("""

        INSERT INTO settings (

            id,
            appointment_minutes,
            buffer_minutes

        )

        VALUES (

            1,
            45,
            30

        )

        """)

    conn.commit()

    conn.close()


def get_all_requests():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM requests
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_requests_as_dicts():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM requests
    """)

    rows = cursor.fetchall()

    conn.close()

    results = []

    for row in rows:

        results.append({

            "id": row[0],
            "client": row[1],
            "phone": row[2],
            "notes": row[3],
            "date": row[4],
            "time": row[5],
            "suggested_price": row[6],
            "approved_price": row[7],
            "approved_on": row[8],
            "status": row[9],
            "file": row[10]

        })

    return results


def insert_request(data):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO requests (

        id,
        client,
        phone,
        notes,
        date,
        time,
        suggested_price,
        approved_price,
        approved_on,
        status,
        file

    )

    VALUES (

        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?

    )

    """, (

        data["id"],
        data["client"],
        data["phone"],
        data["notes"],
        data["date"],
        data["time"],
        data["suggested_price"],
        "",
        "",
        data["status"],
        ""

    ))

    conn.commit()

    conn.close()


def approve_request(
    req_id,
    client,
    date_input,
    time_input,
    price,
    filename
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE requests

    SET

        client = ?,
        date = ?,
        time = ?,
        approved_price = ?,
        approved_on = ?,
        status = ?,
        file = ?

    WHERE id = ?

    """, (

        client,
        date_input,
        time_input,
        price,
        datetime.datetime.now().strftime(
            "%m/%d/%Y %I:%M %p"
        ),
        "approved",
        filename,
        req_id

    ))

    conn.commit()

    conn.close()


def delete_request(req_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE requests

    SET status = 'deleted'

    WHERE id = ?

    """, (req_id,))

    conn.commit()

    conn.close()


def return_to_pending(req_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE requests

    SET status = 'pending'

    WHERE id = ?

    """, (req_id,))

    conn.commit()

    conn.close()


def get_all_business_hours():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT
        id,
        day_of_week,
        start_time,
        end_time,
        active

    FROM business_hours

    ORDER BY id

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def update_business_hour(
    row_id,
    start_time,
    end_time,
    active
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE business_hours

    SET

        start_time = ?,
        end_time = ?,
        active = ?

    WHERE id = ?

    """, (

        start_time,
        end_time,
        active,
        row_id

    ))

    conn.commit()

    conn.close()


def get_scheduler_settings():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT

        appointment_minutes,
        buffer_minutes

    FROM settings

    WHERE id = 1

    """)

    row = cursor.fetchone()

    conn.close()

    return row


def update_scheduler_settings(
    appointment_minutes,
    buffer_minutes
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE settings

    SET

        appointment_minutes = ?,
        buffer_minutes = ?

    WHERE id = 1

    """, (

        appointment_minutes,
        buffer_minutes

    ))

    conn.commit()

    conn.close()


def get_requests_for_date(date_string):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT

        client,
        time,
        status

    FROM requests

    WHERE date = ?
    AND status IN ('pending','approved')

    """, (date_string,))

    rows = cursor.fetchall()

    conn.close()

    return rows


if __name__ == "__main__":

    initialize_database()

    print("Database ready.")