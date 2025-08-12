import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)
SHEET_NAME = "CarPartsDatabase"  # Change to your Google Sheet name
sheet = client.open(SHEET_NAME).sheet1

data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("Car Parts Manager")
st.write("Current Client Data from Google Sheets:")
st.dataframe(df)



