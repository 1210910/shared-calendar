
import os
import sqlite3
from datetime import date, timedelta
from typing import List, Tuple
import pandas as pd
import streamlit as st

# ------------- Config -------------
APP_TITLE = "🎮 Game Night Scheduler"
DB_PATH = "availability.db"
TIME_SLOTS = [
    "Morning (09:00–12:00)",
    "Afternoon (12:00–17:00)",
    "Evening (17:00–21:00)",
    "Late (21:00–01:00)",
]

# ------------- Utilities -------------
def get_password() -> str:
    # Priority: st.secrets["PASSWORD"] -> os.environ["PASSWORD"]
    # If neither exists, default password is "letmein" (documented in README).
    pw = None
    try:
        pw = st.secrets.get("PASSWORD")
    except Exception:
        pw = None
    if not pw:
        pw = os.environ.get("PASSWORD")
    return pw or "letmein"

def init_db() -> None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            name TEXT PRIMARY KEY
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            name TEXT NOT NULL,
            day TEXT NOT NULL,         -- ISO date string YYYY-MM-DD
            slot TEXT NOT NULL,        -- one of TIME_SLOTS
            available INTEGER NOT NULL,
            PRIMARY KEY (name, day, slot),
            FOREIGN KEY (name) REFERENCES users(name)
        );
    """)
    con.commit()
    con.close()

def add_user(name: str) -> None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO users(name) VALUES (?);", (name,))
    con.commit()
    con.close()

def set_availability(name: str, day: str, slot: str, available: bool) -> None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO availability(name, day, slot, available)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(name, day, slot) DO UPDATE SET available=excluded.available;
    """, (name, day, slot, int(available)))
    con.commit()
    con.close()

def get_user_availability(name: str) -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT day, slot, available FROM availability WHERE name = ?;",
        con, params=(name,)
    )
    con.close()
    return df

def get_group_availability(days: List[str]) -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    placeholders = ",".join(["?"]*len(days))
    query = f"""
        SELECT day, slot, SUM(available) AS available_count
        FROM availability
        WHERE day IN ({placeholders})
        GROUP BY day, slot
        ORDER BY day;
    """
    df = pd.read_sql_query(query, con, params=days)
    con.close()
    if df.empty:
        return pd.DataFrame(columns=["day","slot","available_count"])
    return df

def daterange(start: date, end: date):
    for n in range((end - start).days + 1):
        yield start + timedelta(n)

def ensure_css():
    with open("styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# ------------- App -------------
st.set_page_config(page_title=APP_TITLE, page_icon="🎮", layout="wide")
ensure_css()
init_db()

# --------- Auth (shared password) ---------
if "authed" not in st.session_state:
    st.session_state.authed = False
if "username" not in st.session_state:
    st.session_state.username = ""

with st.container():
    st.markdown('<div class="hero"><h1>🎮 Game Night Scheduler</h1><p>Coordinate gaming times with your crew.</p></div>', unsafe_allow_html=True)

if not st.session_state.authed:
    with st.form("login", clear_on_submit=False):
        st.subheader("Login")
        shared_password = st.text_input("Group Password", type="password", help="Same password for everyone in the group.")
        username = st.text_input("Your Name", placeholder="e.g., Alex")
        submit = st.form_submit_button("Enter")

    if submit:
        if not username.strip():
            st.error("Please enter your name.")
        elif shared_password != get_password():
            st.error("Incorrect password. Ask your group owner for the password.")
        else:
            st.session_state.authed = True
            st.session_state.username = username.strip()
            add_user(st.session_state.username)
            st.rerun()
    st.stop()

# --------- Main UI ---------
st.sidebar.subheader("Hello, {}".format(st.session_state.username))
if st.sidebar.button("Log out"):
    st.session_state.authed = False
    st.session_state.username = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**Time slots:**")
for s in TIME_SLOTS:
    st.sidebar.write("• " + s)

col1, col2 = st.columns([3,2], gap="large")

with col1:
    st.subheader("Pick dates")
    today = date.today()
    default_start = today
    default_end = today + timedelta(days=13)

    start_day = st.date_input("Start", value=default_start)
    end_day = st.date_input("End", value=default_end)

    if start_day > end_day:
        st.error("Start date must be before end date.")
        st.stop()

    days = [d.isoformat() for d in daterange(start_day, end_day)]

    st.subheader("Your availability")
    st.caption("Check the slots you can play. Your changes save instantly.")

    # Build an editable grid
    grid_data = []
    user_df = get_user_availability(st.session_state.username)
    existing = {(r["day"], r["slot"]): bool(r["available"]) for _, r in user_df.iterrows()}

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

    # Persist changes
    for _, r in edited.iterrows():
        for slot in TIME_SLOTS:
            set_availability(st.session_state.username, r["Date"], slot, bool(r[slot]))

with col2:
    st.subheader("Group summary")
    group_df = get_group_availability(days)
    if group_df.empty:
        st.info("No availability submitted yet.")
    else:
        # Pivot to a grid day x slot with counts
        pivot = group_df.pivot(index="day", columns="slot", values="available_count").fillna(0).astype(int)
        st.dataframe(pivot, use_container_width=True)

        # Top recommended slots
        st.markdown("**Top slots** (most people available):")
        tall = group_df.sort_values(["available_count", "day", "slot"], ascending=[False, True, True])
        best = tall.head(10)
        if best.empty:
            st.write("No data yet.")
        else:
            for _, r in best.iterrows():
                st.write(f"- {r['day']} — {r['slot']}: **{int(r['available_count'])}** available")

    st.markdown("---")
    st.download_button(
        "⬇️ Export all data (CSV)",
        data=group_df.to_csv(index=False).encode("utf-8"),
        file_name="group_availability.csv",
        mime="text/csv",
        disabled=group_df.empty
    )

st.markdown(
    '<footer class="footer">Made with ❤️ using Streamlit</footer>',
    unsafe_allow_html=True
)
