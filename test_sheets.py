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

# Abrir Google Sheet
sheet_name = "CarPartsDatabase"
spreadsheet = client.open(sheet_name)
worksheet = spreadsheet.get_worksheet(0)

# Mostrar datos actuales
data = worksheet.get_all_records()
df = pd.DataFrame(data)
st.title("📊 Car Parts Database")
st.dataframe(df)

# --- Agregar nueva pieza ---
st.subheader("➕ Agregar nueva pieza")
with st.form("add_part_form"):
    part_name = st.text_input("Nombre de la pieza")
    quantity = st.number_input("Cantidad", min_value=0, step=1)
    price = st.number_input("Precio", min_value=0.0, step=0.01)
    submit = st.form_submit_button("Agregar")

    if submit:
        if part_name.strip() == "":
            st.error("El nombre de la pieza es obligatorio.")
        else:
            worksheet.append_row([part_name, quantity, price])
            st.success(f"✅ Pieza '{part_name}' agregada correctamente.")
            st.rerun()  # Nueva forma
