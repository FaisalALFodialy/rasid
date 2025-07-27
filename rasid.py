from database import create_tables, get_connection
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import re
from back_end import RasidJob, CATEGORY_ID_MAP
from database import fetch_all_users
from database import save_or_update_user


create_tables()


# File to store user registrations
USER_DATA_FILE = "user_data.json"

# Category options
CATEGORIES = [
    "Trade",
    "Contracting",
    "Operation, maintenance, and cleaning of facilities",
    "Real estate and land",
    "Industry, mining, and recycling",
    "Gas, water, and energy",
    "Mines, petroleum, and quarries",
    "Media, publishing, and distribution",
    "Communications and Information Technology",
    "Agriculture and Fishing",
    "Healthcare and Rehabilitation",
    "Education and Training",
    "Employment and Recruitment",
    "Security and Safety",
    "Transportation, Mailing and Storage",
    "Consulting Professions",
    "Tourism, Restaurants, Hotels and Exhibition Organization",
    "Finance, Financing and Insurance"  # ✅ corrected
]


# Frequency options
FREQUENCIES = ["Every Day", "Every Week","Every Month"]

# Helper to load/save user data
def load_user(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "email": row[0],
            "company_name": row[1],
            "category": row[2],
            "schedule": {
                "frequency": row[3],
                "start_date": row[4],
                "start_time": row[5],
                "last_updated": row[6]
            } if row[3] else None
        }
    return None



def save_or_update_user(email, company_name, category, schedule=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone()

    if schedule:
        frequency = schedule["frequency"]
        start_date = schedule["start_date"]
        start_time = schedule["start_time"]
        last_updated = schedule["last_updated"]
    else:
        frequency = start_date = start_time = last_updated = None

    if exists:
        cursor.execute("""
            UPDATE users
            SET company_name=?, category=?, frequency=?, start_date=?, start_time=?, last_updated=?
            WHERE email=?
        """, (company_name, category, frequency, start_date, start_time, last_updated, email))
    else:
        cursor.execute("""
            INSERT INTO users (email, company_name, category, frequency, start_date, start_time, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email, company_name, category, frequency, start_date, start_time, last_updated))

    conn.commit()
    conn.close()

# App title
st.set_page_config(page_title="Rasid - Opportunity Tracker")
st.title("راصد (Rasid) – Opportunity Tracker")

# Sidebar for navigation
st.sidebar.image("rasid.png", use_container_width=True)
st.sidebar.title("About")
st.sidebar.info(
    "This intelligent Web Scraping tool is designed to recommend best Opportunities for Company."
)
menu = st.sidebar.selectbox("Navigation", ["Register", "Login", "Schedule Opportunities"])

user_data = fetch_all_users()  # This returns a dict-like object
session_email = st.session_state.get("logged_in_email")
if menu == "Register":
    st.header("Register Your Company")
    company_name = st.text_input("Company Name")
    email = st.text_input("Company Email")
    category = st.selectbox("Company Category", CATEGORIES)

    if st.button("Register"):
        email = email.strip()
        company_name = company_name.strip()

        if not company_name.strip() or not email.strip():
            st.error("Please fill in all fields.")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Please enter a valid email address.")
        elif email in user_data:
            st.error("This email is already registered.")
        else:
            user_data[email] = {
                "company_name": company_name,
                "category": category,
                "schedule": None
            }
            save_or_update_user(email, company_name, category)
            st.success("✅ Company registered successfully! You can now login.")



elif menu == "Login":
    st.header("Login")
    login_email = st.text_input("Enter your email")
    if st.button("Login"):
        if login_email in user_data:
            st.session_state.logged_in_email = login_email
            st.success(f"Welcome {user_data[login_email]['company_name']}")
        else:
            st.error("Email not registered.")

elif menu == "Schedule Opportunities":
    st.header("Set Up Opportunity Notifications")
    if session_email:
        company_info = user_data[session_email]
        st.markdown(f"**Company:** {company_info['company_name']}")
        category = st.selectbox("Select Category", CATEGORIES, index=CATEGORIES.index(company_info['category']))
        start_date = st.date_input("📅 Schedule Start Date", value=datetime.today())
        if "preferred_time" not in st.session_state:
            st.session_state.preferred_time = datetime.now().time()

        start_time = st.time_input("⏰ Preferred Time", value=st.session_state.preferred_time)
        frequency = st.selectbox("Send Opportunities", FREQUENCIES)


        if st.button("Submit Schedule"):
            user_data[session_email]["category"] = category

            # Save to database
            save_or_update_user(
                email=session_email,
                company_name=company_info['company_name'],
                category=category,
                schedule={
                    "frequency": frequency,
                    "start_date": str(start_date),
                    "start_time": str(start_time),
                    "last_updated": datetime.now().isoformat()
                }
            )


            st.success("Schedule preferences saved! for now you will receive updates via email after 3-4 minutes.")
            
            try:
                job = RasidJob(
                    sender_email="rasid.projects.news@gmail.com",
                    password = "sveiheahhbzidbnf",
                    company_name=company_info['company_name'],
                    client_email=session_email,  # ✅ CORRECT
                    category=category,
                    start_date= str(start_date),
                    time_of_day=start_time,
                    frequency=frequency
                )
                job.run()
            except ValueError as ve:
                st.error(str(ve))
            except Exception as e:
                st.error(f"Unexpected error: {e}")
