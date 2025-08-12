import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Configuración Google Sheets ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)
client = gspread.authorize(creds)

SHEET_NAME = "CarPartsDatabase"
worksheet = client.open(SHEET_NAME).sheet1

# --- Cargar datos ---
data = worksheet.get_all_records()
df = pd.DataFrame(data)

st.title("🛠️ Car Parts Manager")

st.subheader("📋 Lista de piezas")
st.dataframe(df)

# --- Inicializar valores de formulario si no existen ---
if "part_name" not in st.session_state:
    st.session_state.part_name = ""
if "quantity" not in st.session_state:
    st.session_state.quantity = 0
if "price" not in st.session_state:
    st.session_state.price = 0.0

# --- Agregar nueva pieza ---
st.subheader("➕ Agregar nueva pieza")
with st.form("add_part_form"):
    part_name = st.text_input("Nombre de la pieza", key="part_name")
    quantity = st.number_input("Cantidad", min_value=0, step=1, key="quantity")
    price = st.number_input("Precio", min_value=0.0, step=0.01, key="price")
    submit = st.form_submit_button("Agregar")

    if submit:
        if part_name.strip() == "":
            st.error("⚠️ El nombre de la pieza es obligatorio.")
        else:
            worksheet.append_row([part_name, quantity, price])
            st.success(f"✅ Pieza '{part_name}' agregada correctamente.")

            # Limpiar campos antes de recargar
            st.session_state.part_name = ""
            st.session_state.quantity = 0
            st.session_state.price = 0.0

            st.rerun()
