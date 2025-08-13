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
    return int(df_index) + 2

# --- Connect to Google Sheets ---
try:
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=SCOPE
    )
    client = gspread.authorize(creds)
    SHEET_NAME = "CarPartsDatabase"  # Change if needed
    worksheet = client.open(SHEET_NAME).sheet1
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

    # Search bar before adding, so you can check if client exists
    st.markdown("**Search Clients** (by name or phone)")
    search_term = st.text_input("Enter name or phone to search")
    df_view = df_all.copy()
    if search_term:
        if "Client Name" in df_view.columns and "Phone" in df_view.columns:
            df_view["Client Name"] = df_view["Client Name"].astype(str).fillna("")
            df_view["Phone"] = df_view["Phone"].astype(str).fillna("")
            df_view = df_view[
                df_view["Client Name"].str.contains(search_term, case=False, na=False) |
                df_view["Phone"].str.contains(search_term, case=False, na=False)
            ]
        st.dataframe(df_view if not df_view.empty else pd.DataFrame())

    # Add new client form
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
    st.subheader("Search and Edit Client")
    if df_all.empty:
        st.info("No records to edit.")
    elif not {"Phone", "Client Name"}.issubset(df_all.columns):
        st.error("❌ 'Phone' or 'Client Name' column not found. Please check sheet headers.")
    else:
        search_edit = st.text_input("Search by name or phone")
        df_edit = df_all.copy()
        if search_edit:
            df_edit["Client Name"] = df_edit["Client Name"].astype(str).fillna("")
            df_edit["Phone"] = df_edit["Phone"].astype(str).fillna("")
            df_edit = df_edit[
                df_edit["Client Name"].str.contains(search_edit, case=False, na=False) |
                df_edit["Phone"].str.contains(search_edit, case=False, na=False)
            ]

        if not df_edit.empty:
            st.dataframe(df_edit)
            phone_options = df_edit["Phone"].astype(str).dropna().unique().tolist()
            selected_phone = st.selectbox("Select client by phone", [""] + sorted(phone_options))

            if selected_phone:
                match = df_all[df_all["Phone"].astype(str) == selected_phone]
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
        else:
            st.info("No matching records found.")
