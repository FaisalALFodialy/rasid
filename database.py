import sqlite3

def get_connection():
    conn = sqlite3.connect("rasid.db", check_same_thread=False)
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            company_name TEXT,
            category TEXT,
            frequency TEXT,
            start_date TEXT,
            start_time TEXT,
            last_updated TEXT
        )
    """)
    conn.commit()
    conn.close()


def fetch_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    data = {}
    for row in rows:
        email, company_name, category, frequency, start_date, start_time, last_updated = row
        data[email] = {
            "company_name": company_name,
            "category": category,
            "schedule": {
                "frequency": frequency,
                "start_date": start_date,
                "start_time": start_time,
                "last_updated": last_updated
            } if frequency else None
        }
    return data

def save_or_update_user(email, company_name, category, frequency, start_date, start_time, last_updated):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (email, company_name, category, frequency, start_date, start_time, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            company_name=excluded.company_name,
            category=excluded.category,
            frequency=excluded.frequency,
            start_date=excluded.start_date,
            start_time=excluded.start_time,
            last_updated=excluded.last_updated;
    """, (email, company_name, category, frequency, start_date, start_time, last_updated))
    conn.commit()
    conn.close()

