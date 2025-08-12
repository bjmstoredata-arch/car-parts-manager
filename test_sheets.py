import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)

st.write("Service Account Email:", creds.service_account_email)
