import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Nombre de la hoja en Google Sheets
SHEET_NAME = "CarPartsDatabase"

# Alcances necesarios
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Cargar credenciales desde secrets
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)

# Autenticación con gspread
client = gspread.authorize(creds)

try:
    # Abrir la hoja
    sheet = client.open(SHEET_NAME).sheet1

    # Obtener todos los registros
    data = sheet.get_all_records()

    # Convertir a DataFrame
    df = pd.DataFrame(data)

    st.title("Car Parts Manager")
    st.subheader("Datos actuales desde Google Sheets")
    st.dataframe(df)

except gspread.SpreadsheetNotFound:
    st.error(f"No se encontró la hoja '{SHEET_NAME}'. "
             "Verifica que el service account tenga acceso como Editor.")
