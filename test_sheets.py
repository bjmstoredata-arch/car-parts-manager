import streamlit as st
import pandas as pd
import gspread
import json
from io import StringIO
from oauth2client.service_account import ServiceAccountCredentials

# 🔐 Google Sheets setup using Streamlit Secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
json_key = json.dumps(dict(st.secrets["gcp"]))  # ✅ Convert AttrDict to dict
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp"]), scope)

client = gspread.authorize(creds)
sheet = client.open("CarPartsDatabase").worksheet("VinRecords")  # ✅ Your actual sheet name

# 📥 Load data from sheet
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# 🧾 Save VIN entry
def save_vin(phone, vin):
    sheet.append_row([phone, vin, pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "", "", ""])

# 🔄 Update vehicle details for a given VIN
def update_vehicle_details(vin, model, prod_yr, body, engine, code, transmission):
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if row["VIN No"] == vin:
            sheet.update_cell(i + 2, 4, model)
            sheet.update_cell(i + 2, 5, prod_yr)
            sheet.update_cell(i + 2, 6, body)
            sheet.update_cell(i + 2, 7, engine)
            sheet.update_cell(i + 2, 8, code)
            sheet.update_cell(i + 2, 9, transmission)
            break

# 🚀 Streamlit UI
st.title("Client Vehicle Entry")

# Step 1: Save VIN
with st.form("vin_form"):
    phone = st.text_input("📱 Phone")
    vin = st.text_input("🔍 VIN No")
    submitted_vin = st.form_submit_button("Save VIN")
    if submitted_vin and phone and vin:
        save_vin(phone, vin)
        st.session_state["vin_saved"] = vin
        st.success(f"✅ VIN {vin} saved. Now enter vehicle details.")

# Step 2: Add Vehicle Details
if "vin_saved" in st.session_state:
    with st.form("vehicle_form"):
        st.subheader(f"🚗 Add details for VIN: {st.session_state['vin_saved']}")
        model = st.text_input("Model")
        prod_yr = st.text_input("Prod. Yr")
        body = st.text_input("Body")
        engine = st.text_input("Engine")
        code = st.text_input("Code")
        transmission = st.text_input("Transmission")
        submitted_details = st.form_submit_button("Save Vehicle Details")
        if submitted_details:
            update_vehicle_details(
                st.session_state["vin_saved"],
                model, prod_yr, body, engine, code, transmission
            )
            st.success("✅ Vehicle details saved.")
            del st.session_state["vin_saved"]

