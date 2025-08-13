import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Google Sheets configuration ---
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
    st.error(f"Could not connect to Google Sheets: {e}")
    st.stop()

# --- Load data ---
try:
data = worksheet.get_all_records()
df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Error loading data: {e}")
st.stop()

st.title("🛠️ Car Parts Manager")

st.subheader("📋 Parts List")
if not df.empty:
    #fomat price colum if it exist
    if "Price" in df.columns:
            df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0.0)
            df["Price"] = df["Price"].apply(lambda x: f"${x:.2f}")
        st.dataframe(df)
    else:
        st.info("No parts found in the database.")

