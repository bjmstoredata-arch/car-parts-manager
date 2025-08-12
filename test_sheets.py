import gspread
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Cargar credenciales desde Streamlit secrets
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

# Crear una nueva hoja
sheet = client.create("CarPartsDatabase")

# Compartirla con el mismo service account (no siempre es necesario)
sheet.share(
    st.secrets["google_service_account"]["client_email"],
    perm_type='user',
    role='owner'
)

print(f"Hoja creada: {sheet.url}")
