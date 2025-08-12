import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

# List all spreadsheets the service account can see
files = client.list_spreadsheet_files()
st.write("Sheets the service account can access:")
for f in files:
    st.write(f["name"])
