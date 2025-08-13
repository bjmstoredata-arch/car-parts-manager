import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

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

# --- Search Functionality (by phone number only) ---
st.subheader("🔍 Search by Phone Number")
search_phone = st.text_input("Enter phone number to search")
if search_phone:
    if "Phone Number" in df.columns:
        df["Phone Number"] = df["Phone Number"].astype(str).fillna("")
        df = df[df["Phone Number"].str.contains(search_phone, case=False, na=False)]
    else:
        st.warning("⚠️ 'Phone Number' column not found in the data.")

# --- Format Price Column ---
if not df.empty:
    if "Price" in df.columns:
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0.0)
        df["Price"] = df["Price"].apply(lambda x: f"${x:.2f}")
    st.subheader("📋 Parts List")
    st.dataframe(df)
else:
    st.info("No parts found in the database.")

# --- Initialize session state for form fields ---
for field, default in {
    "part_name": "",
    "quantity": 0,
    "price": 0.0,
    "phone_number": ""
}.items():
    if field not in st.session_state:
        st.session_state[field] = default

# --- Add new part ---
st.subheader("➕ Add a New Part")
with st.form("add_part_form"):
    part_name = st.text_input("Part Name", key="part_name")
    quantity = st.number_input("Quantity", min_value=0, step=1, key="quantity")
    price = st.number_input("Price", min_value=0.0, step=0.01, key="price")
    phone_number = st.text_input("Phone Number", key="phone_number")
    submit = st.form_submit_button("Add")

if submit:
    if part_name.strip() == "":
        st.error("⚠️ Part name is required.")
    elif quantity <= 0 or price <= 0:
        st.error("⚠️ Quantity and price must be greater than zero.")
    elif phone_number.strip() == "":
        st.error("⚠️ Phone number is required.")
    else:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, part_name, quantity, price, phone_number])
            st.success(f"✅ Part '{part_name}' added successfully.")
            # Reset form fields
            st.session_state.part_name = ""
            st.session_state.quantity = 0
            st.session_state.price = 0.0
            st.session_state.phone_number = ""
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error adding part: {e}")
