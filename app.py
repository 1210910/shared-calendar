# This is a ready-to-deploy Streamlit project with tabs for scheduling and slot summary.
# File structure:
# game-night-scheduler/
# ├─ app.py  (main app)
# ├─ styles.css  (UI styling)
# ├─ requirements.txt  (dependencies)
# ├─ README.md
# └─ .streamlit/config.toml  (theme settings)

# ---------------- app.py ----------------
import sqlite3
from datetime import date, timedelta
from typing import List
import os
import pandas as pd
import streamlit as st

# ---------- Config ----------
APP_TITLE = "🎮 Game Night Scheduler"
DB_PATH = "availability.db"
TIME_SLOTS = [
    "Morning (09:00–12:00)",
    "Afternoon (12:00–17:00)",
    "Evening (17:00–21:00)",
    "Late (21:00–01:00)",
]

# ---------- Utilities ----------
def get_password() -> str:
    pw = None
    try:
        pw = st.secrets.get("PASSWORD")
    except Exception:
        pw = None
    if not pw:
        pw = os.environ.get("PASSWORD")
    return pw or "letmein"

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY);")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            name TEXT NOT NULL,
            day TEXT NOT NULL,
            slot TEXT NOT NULL,
            available INTEGER NOT NULL,
            PRIMARY KEY (name, day, slot),
            FOREIGN KEY (name) REFERENCES users(name)
        );
    """)
    con.commit()
    con.close()

def add_user(name: str):
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT OR IGNORE INTO users(name) VALUES (?);", (name,))
    con.commit()
    con.close()

def set_availability(name: str, day: str, slot: str, available: bool):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT INTO availability(name, day, slot, available)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(name, day, slot) DO UPDATE SET available=excluded.available;
    """, (name, day, slot, int(available)))
    con.commit()
    con.close()

def get_user_availability(name: str) -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT day, slot, available FROM availability WHERE name = ?;", con, params=(name,))
    con.close()
    return df

def get_slot_members(day: str, slot: str) -> List[str]:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name FROM availability WHERE day=? AND slot=? AND available=1;", con, params=(day, slot))
    con.close()
    return df["name"].tolist()

def daterange(start: date, end: date):
    for n in range((end - start).days + 1):
        yield start + timedelta(n)

# ---------- App ----------
st.set_page_config(page_title=APP_TITLE, page_icon="🎮", layout="wide")
init_db()

# ---------- Auth ----------
if "authed" not in st.session_state:
    st.session_state.authed = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authed:
    with st.form("login", clear_on_submit=False):
        st.subheader("Login")
        username = st.text_input("Your Name", placeholder="e.g., Alex")
        shared_password = st.text_input("Group Password", type="password")
        submit = st.form_submit_button("Enter")

    if submit:
        if not username.strip():
            st.error("Please enter your name.")
        elif shared_password != get_password():
            st.error("Incorrect password.")
        else:
            st.session_state.authed = True
            st.session_state.username = username.strip()
            add_user(st.session_state.username)
            st.experimental_rerun()
    st.stop()

# ---------- Main ----------
st.sidebar.subheader(f"Hello, {st.session_state.username}")
if st.sidebar.button("Log out"):
    st.session_state.authed = False
    st.session_state.username = ""
    st.experimental_rerun()

# Date range selection
today = date.today()
default_start = today
default_end = today + timedelta(days=13)
start_day = st.sidebar.date_input("Start Date", value=default_start)
end_day = st.sidebar.date_input("End Date", value=default_end)
if start_day > end_day:
    st.sidebar.error("Start date must be before end date.")
    st.stop()
days = [d.isoformat() for d in daterange(start_day, end_day)]

# Tabs
tab1, tab2 = st.tabs(["🗓️ Schedule", "👥 Slot Summary"])

# ---------- Tab 1: Schedule ----------
with tab1:
    st.subheader("Your Availability")
    user_df = get_user_availability(st.session_state.username)
    existing = {(r["day"], r["slot"]): bool(r["available"]) for _, r in user_df.iterrows()}

    grid_data = []
    for d in days:
        row = {"Date": d}
        for slot in TIME_SLOTS:
            row[slot] = existing.get((d, slot), False)
        grid_data.append(row)

    edited = st.data_editor(
        pd.DataFrame(grid_data),
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        column_config={slot: st.column_config.CheckboxColumn() for slot in TIME_SLOTS},
        key="availability_editor",
    )

    for _, r in edited.iterrows():
        for slot in TIME_SLOTS:
            set_availability(st.session_state.username, r["Date"], slot, bool(r[slot]))

# ---------- Tab 2: Slot Summary ----------
with tab2:
    st.subheader("Who is available for each slot")
    if not days:
        st.info("No days selected.")
    else:
        for d in days:
            st.markdown(f"**{d}**")
            for slot in TIME_SLOTS:
                members = get_slot_members(d, slot)
                st.write(f"- {slot}: {', '.join(members) if members else 'No one available'}")
