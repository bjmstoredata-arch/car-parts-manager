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

# --- Add a new record ---
st.subheader("➕ Add a New Record")
with st.form("add_record_form"):
    client_name = st.text_input("Client Name")
    phone = st.text_input("Phone")
    vin_no = st.text_input("Vin No")
    model = st.text_input("Model")
    prod_yr = st.text_input("Prod. Yr")
    body = st.text_input("Body")
    engine = st.text_input("Engine")
    code = st.text_input("Code")
    transmission = st.text_input("Transmission")
    submit = st.form_submit_button("Add")

if submit:
    if phone.strip() == "":
        st.error("⚠️ Phone number is required.")
    else:
        try:
            date_str = datetime.now().strftime("%d/%m/%Y")
            vin_no_upper = vin_no.strip().upper() if vin_no else ""
            worksheet.append_row([
                date_str, client_name, phone, vin_no_upper, model,
                prod_yr, body, engine, code, transmission
            ])
            st.success(f"✅ Record saved for phone: {phone}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error adding record: {e}")

# --- Edit an existing record ---
st.subheader("✏️ Edit Client")
if not df.empty:
    phones = df["Phone"].dropna().unique().tolist()
    selected_phone = st.selectbox("Select client by phone", [""] + phones)

    if selected_phone:
        row_index = df.index[df["Phone"] == selected_phone][0] + 2  # +2 because gspread rows start at 1 and have headers
        record = df[df["Phone"] == selected_phone].iloc[0]

        with st.form("edit_form"):
            client_name_e = st.text_input("Client Name", record["Client Name"])
            phone_e = st.text_input("Phone", record["Phone"])
            vin_no_e = st.text_input("Vin No", record["Vin No"])
            model_e = st.text_input("Model", record["Model"])
            prod_yr_e = st.text_input("Prod. Yr", record["Prod. Yr"])
            body_e = st.text_input("Body", record["Body"])
            engine_e = st.text_input("Engine", record["Engine"])
            code_e = st.text_input("Code", record["Code"])
            transmission_e = st.text_input("Transmission", record["Transmission"])
            save_changes = st.form_submit_button("Save Changes")

        if save_changes:
            try:
                vin_no_e = vin_no_e.strip().upper() if vin_no_e else ""
                worksheet.update(f"A{row_index}:J{row_index}", [[
                    record["Date"], client_name_e, phone_e, vin_no_e,
                    model_e, prod_yr_e, body_e, engine_e, code_e, transmission_e
                ]])
                st.success("✅ Client record updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating record: {e}")
