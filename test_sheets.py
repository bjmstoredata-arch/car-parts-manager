import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
client = gspread.authorize(creds)

# Print the email
st.write("Service account email:", creds.service_account_email)

# List all accessible spreadsheets
files = client.list_spreadsheet_files()
if files:
    st.write("Sheets the service account can access:")
    for f in files:
        st.write(f["name"], "-", f["id"])
else:
    st.write("No spreadsheets found. Make sure the service account has access.")
