import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Google API scope
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit secrets
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

# Page title
st.title("Google Sheets Access Test")

st.write("Sheets the service account can access:")

try:
    files = client.list_spreadsheet_files()
    if files:
        for f in files:
            st.write(f["name"])
    else:
        st.warning("No spreadsheets found. Make sure the service account has access.")
except Exception as e:
    st.error(f"Error: {e}")
