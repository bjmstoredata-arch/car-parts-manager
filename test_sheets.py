import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import altair as alt

# --- Google Sheets Configuration ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=SCOPE
    )
    client = gspread.authorize(creds)
    SHEET_NAME = "CarPartsDatabase"
    worksheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"❌ Could not connect to Google Sheets: {e}")
    st.stop()

# --- Load data ---
try:
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

st.title("🛠️ Car Parts Manager")

# --- Search Functionality ---
st.subheader("🔍 Search Parts")
search_term = st.text_input("Enter part name to search")
if search_term:
    df = df[df["Part Name"].str.contains(search_term, case=False, na=False)]

# --- Format Price Column ---
if not df.empty:
    if "Price" in df.columns:
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0.0)
        df["Price"] = df["Price"].apply(lambda x: f"${x:.2f}")
    st.subheader("📋 Parts List")
    st.dataframe(df)
else:
    st.info("No parts found in the database.")

# --- Quantity Chart ---
if not df.empty and "Quantity" in df.columns and "Part Name" in df.columns:
    st.subheader("📊 Quantity Overview")
    chart = alt.Chart(df).mark_bar().encode(
        x="Part Name",
        y="Quantity"
    )
    st.altair_chart(chart, use_container_width=True)

# --- Initialize session state for form fields ---
for field, default in {
    "part_name": "",
    "quantity": 0,
    "price": 0.0
}.items():
    if field not in st.session_state:
        st.session_state[field] = default

# --- Add new part ---
st.subheader("➕ Add a New Part")
with st.form("add_part_form"):
    part_name = st.text_input("Part Name", key="part_name")
    quantity = st.number_input("Quantity", min_value=0, step=1, key="quantity")
    price = st.number_input("Price", min_value=0.0, step=0.01, key="price")
    submit = st.form_submit_button("Add")

if submit:
    if part_name.strip() == "":
        st.error("⚠️ Part name is required.")
    elif quantity <= 0 or price <= 0:
        st.error("⚠️ Quantity and price must be greater than zero.")
    elif "Part Name" in df.columns and part_name.lower() in df["Part Name"].str.lower().tolist():
        st.warning("⚠️ This part already exists in the database.")
    else:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, part_name, quantity, price])
            st.success(f"✅ Part '{part_name}' added successfully.")
            # Reset form fields
            st.session_state.part_name = ""
            st.session_state.quantity = 0
            st.session_state.price = 0.0
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error adding part: {e}")
