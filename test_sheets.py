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

st.title("📄 Crear Google Sheet de prueba")

# Botón para crear la hoja
if st.button("Crear nueva hoja 'CarPartsDatabase'"):
    sheet = client.create("CarPartsDatabase")
    st.success(f"✅ Hoja creada: {sheet.url}")
    
    # Escribir datos de ejemplo
    worksheet = sheet.get_worksheet(0)  # Primera pestaña
    worksheet.update(
        "A1",
        [["Part Name", "Quantity", "Price"],
         ["Brake Pad", 10, 25.50],
         ["Oil Filter", 15, 8.99]]
    )
    
    st.info("📊 Datos de ejemplo agregados.")

# Mostrar lista de hojas accesibles
st.subheader("Hojas accesibles por este service account:")
files = client.list_spreadsheet_files()
if files:
    for f in files:
        st.write(f"- {f['name']}: {f['url']}")
else:
    st.warning("No se encontraron hojas accesibles.")
