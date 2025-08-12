# test_sheets.py
import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

SERVICE_ACCOUNT_FILE = "steel-shine-468815-s3-f663e899ceff.json"   # your downloaded JSON
SPREADSHEET_ID = "1oU5NWgDkggNMGQkONmgcrpmWGViLWIBZwwCnFlFgUWg"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]


creds_dict = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

gc = gspread.authorize(creds)

# open by id and print first sheet rows
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.sheet1  # first worksheet/tab
print("Title:", sh.title)
print("First 10 rows:")
print(ws.get_all_values()[:10])
