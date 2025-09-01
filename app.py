# This is a ready-to-deploy Streamlit project with tabs for scheduling and slot summary.
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
