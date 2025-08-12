import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Read from Streamlit Secrets
creds_dict = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
