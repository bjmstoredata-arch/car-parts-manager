import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Google Sheets Setup ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from file
creds = Credentials.from_service_account_file(
    "service_account.json",  # The JSON file you downloaded
    scopes=SCOPE
)

# Connect to Google Sheets
client = gspread.authorize(creds)

# Open your spreadsheet
SHEET_NAME = "CarPartsDatabase"  # Change to your Google Sheet name
sheet = client.open(SHEET_NAME).sheet1

# Read all data
data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- Streamlit UI ---
st.title("Car Parts Manager")
st.write("Current Client Data from Google Sheets:")
st.dataframe(df)
