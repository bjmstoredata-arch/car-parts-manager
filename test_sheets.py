import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Cargar credenciales
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

# Abrir la hoja por nombre
sheet_name = "CarPartsDatabase"
spreadsheet = client.open(sheet_name)

# Seleccionar la primera hoja de la spreadsheet
worksheet = spreadsheet.get_worksheet(0)

# Obtener todos los valores
data = worksheet.get_all_records()

# Convertir a DataFrame
df = pd.DataFrame(
