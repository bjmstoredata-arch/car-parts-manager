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
    SHEET_NAME = "CarPartsDatabase"  # Change if needed
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

# Title
st.title("📑 Cliente Info")

# --- Search by Phone ---
st.subheader("🔍 Search by Phone Number")
search_phone = st.text_input("Enter phone number to search")
if search_phone:
    if "Phone" in df.columns:
        df["Phone"] = df["Phone"].astype(str).fillna("")
        df = df[df["Phone"].str.contains(search_phone, case=False, na=False)]
    else:
        st.warning("⚠️ 'Phone' column not found in the data.")

# --- Show Table ---
if not df.empty:
    st.subheader("📋 Records")
    st.dataframe(df)
else:
    st.info("No matching records found.")

# --- Initialize form state ---
form_defaults = {
    "client_name": "",
    "phone": "",
    "vin_no": "",
    "model": "",
    "prod_yr": "",
    "body": "",
    "engine": "",
    "code": "",
    "transmission": ""
}
for field, default in form_defaults.items():
    if field not in st.session_state:
        st.session_state[field] = default

# --- Add a new record ---
st.subheader("➕ Add a New Record")
with st.form("add_record_form"):
    client_name = st.text_input("Client Name", key="client_name")
    phone = st.text_input("Phone", key="phone")
    vin_no = st.text_input("Vin No", key="vin_no")
    model = st.text_input("Model", key="model")
    prod_yr = st.text_input("Prod. Yr", key="prod_yr")
    body = st.text_input("Body", key="body")
    engine = st.text_input("Engine", key="engine")
    code = st.text_input("Code", key="code")
    transmission = st.text_input("Transmission", key="transmission")
    submit = st.form_submit_button("Add")

if submit:
    if phone.strip() == "":
        st.error("⚠️ Phone number is required.")
    else:
        try:
            date_str = datetime.now().strftime("%d/%m/%Y")  # Auto date
            vin_no_upper = vin_no.strip().upper() if vin_no else ""
            worksheet.append_row([
                date_str, client_name, phone, vin_no_upper, model,
                prod_yr, body, engine, code, transmission
            ])
            st.success(f"✅ Record added successfully for phone: {phone}")
            # Reset form fields
            for field in form_defaults.keys():
                st.session_state[field] = ""
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error adding record: {e}")
