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

# Autenticación
client = gspread.authorize(creds)

st.title("Google Sheets Access Test")

# Listar hojas disponibles para el service account
try:
    files = client.list_spreadsheet_files()
    if files:
        st.write("Sheets the service account can access:")
        for f in files:
            st.write(f"📄 {f['name']} (ID: {f['id']})")
    else:
        st.warning("No spreadsheets found. Make sure the service account has access.")
except Exception as e:
    st.error(f"Error listing spreadsheets: {e}")
