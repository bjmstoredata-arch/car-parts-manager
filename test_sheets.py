import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Cargar credenciales desde secrets
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

# Listar hojas que puede ver el service account
st.title("Google Sheets Access Test")
st.write("Sheets the service account can access:")

for spreadsheet in client.openall():
    st.write("-", spreadsheet.title)
