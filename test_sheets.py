import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

HEADERS = ["Date", "Client Name", "Phone"]

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def normalize_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df.columns = [c.strip() for c in df.columns]
    syn = {
        "date": "Date",
        "client name": "Client Name",
        "phone": "Phone",
        "phone number": "Phone",
        "mobile": "Phone"
    }
    rename_map = {c: syn[c.lower()] for c in df.columns if c.lower() in syn}
    return df.rename(columns=rename_map)

def get_row_index_for_df_index(df_index: int) -> int:
    return int(df_index) + 2  # 1 for headers + 1 for 1-based index

# --- Connect to Google Sheets ---
try:
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=SCOPE
    )
    client = gspread.authorize(creds)
    SHEET_NAME = "CarPartsDatabase"  # change if needed
    worksheet = client.open(SHEET_NAME).Clients
except Exception as e:
    st.error(f"❌ Could not connect to Google Sheets: {e}")
    st.stop()

# --- Load Data ---
try:
    data = worksheet.get_all_records()
    df_all = normalize_and_rename_columns(pd.DataFrame(data))
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

st.title("📑 Client Info")

# --- Tabs ---
tab_add, tab_edit = st.tabs(["➕ Add Client", "✏️ Edit Client"])

with tab_add:
    st.subheader("Add New Client")
    with st.form("add_client_form"):
        client_name = st.text_input("Client Name")
        phone = st.text_input("Phone")
        submit_add = st.form_submit_button("Add Client")

    if submit_add:
        if phone.strip() == "":
            st.error("⚠️ Phone number is required.")
        else:
            try:
                date_str = datetime.now().strftime("%d/%m/%Y")
                worksheet.append_row([date_str, client_name, phone])
                st.success(f"✅ Record saved for phone: {phone}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error adding client: {e}")

with tab_edit:
    st.subheader("Select and Edit Client")
    if df_all.empty:
        st.info("No records to edit.")
    elif "Phone" not in df_all.columns:
        st.error("❌ 'Phone' column not found. Please check your sheet headers.")
    else:
        phone_options = sorted(df_all["Phone"].astype(str).dropna().unique().tolist())
        selected_phone = st.selectbox("Select client by phone", [""] + phone_options)

        if selected_phone:
            match = df_all[df_all["Phone"].astype(str) == str(selected_phone)]
            if not match.empty:
                selected_df = match.iloc[0]
                selected_idx = match.index[0]

                with st.form("edit_client_form"):
                    client_name_e = st.text_input("Client Name", selected_df.get("Client Name", ""))
                    phone_e = st.text_input("Phone", selected_df.get("Phone", ""))
                    save_changes = st.form_submit_button("Save Changes")

                if save_changes:
                    if phone_e.strip() == "":
                        st.error("⚠️ Phone number is required.")
                    else:
                        try:
                            row_index = get_row_index_for_df_index(selected_idx)
                            date_keep = str(selected_df.get("Date", ""))
                            worksheet.update(f"A{row_index}:C{row_index}", [[date_keep, client_name_e, phone_e]])
                            st.success("✅ Client updated successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error updating client: {e}")

