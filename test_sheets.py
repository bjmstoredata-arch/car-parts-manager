import streamlit as st
import gspread
import pandas as pd
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

# Abrir la hoja
sheet_name = "CarPartsDatabase"
spreadsheet = client.open(sheet_name)

# Tomar la primera pestaña
worksheet = spreadsheet.get_worksheet(0)

# Leer todos los datos
data = worksheet.get_all_records()

# Convertir a DataFrame y mostrarlo
df = pd.DataFrame(data)
st.title("📊 Car Parts Database")
st.dataframe(df)
