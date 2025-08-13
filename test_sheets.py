import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Expected Google Sheet headers (in this order) ---
HEADERS = ["Date", "Client Name", "Phone", "Vin No"]

# --- Google Sheets configuration ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_row_index_for_df_index(df_index: int) -> int:
    # +1 for header row, +1 for 1-based indexing
    return int(df_index) + 2

def load_dataframe(worksheet) -> pd.DataFrame:
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    # Normalize header whitespace just in case
    df.columns = [c.strip() for c in df.columns]
    return df

def find_last_row_index_by_phone(worksheet, phone: str) -> int | None:
    """Find the last matching row index (1-based) in the sheet for a given phone."""
    df = load_dataframe(worksheet)
    if "Phone" not in df.columns:
        return None
    matches = df[df["Phone"].astype(str) == str(phone)]
    if matches.empty:
        return None
    last_df_index = matches.index[-1]
    return get_row_index_for_df_index(last_df_index)

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

# --- Load data safely ---
try:
    df_all = load_dataframe(worksheet)
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# Gentle heads-up if headers aren't as expected
if list(worksheet.row_values(1)[:len(HEADERS)]) != HEADERS:
    st.info("ℹ️ Make sure your sheet headers (row 1) are exactly: " + " | ".join(HEADERS))

st.title("📑 Client Info")

# Session flags for VIN step
if "pending_vin_phone" not in st.session_state:
    st.session_state.pending_vin_phone = None
if "pending_vin_row" not in st.session_state:
    st.session_state.pending_vin_row = None

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
                # Append in the exact header order: Date, Client Name, Phone, Vin No
                date_str = datetime.now().strftime("%d/%m/%Y")
                worksheet.append_row([date_str, client_name, phone, ""])
                # Prepare VIN Next step
                st.session_state.pending_vin_phone = phone
                # Find the row we just appended (last match for this phone)
                row_index = find_last_row_index_by_phone(worksheet, phone)
                st.session_state.pending_vin_row = row_index
                st.success(f"✅ Client saved for phone: {phone}. Next: add VIN below.")
            except Exception as e:
                st.error(f"❌ Error adding client: {e}")

    # VIN Next step (appears after adding)
    if st.session_state.pending_vin_phone:
        st.divider()
        st.subheader("Next: Add VIN")
        st.caption(f"For client phone: {st.session_state.pending_vin_phone}")
        with st.form("vin_after_add_form"):
            vin_no = st.text_input("VIN No")
            save_vin = st.form_submit_button("Save VIN")
        if save_vin:
            if vin_no.strip() == "":
                st.error("⚠️ VIN cannot be empty.")
            else:
                try:
                    target_row = st.session_state.pending_vin_row
                    # Fallback: look up row by phone if not set
                    if not target_row:
                        target_row = find_last_row_index_by_phone(worksheet, st.session_state.pending_vin_phone)
                    if not target_row:
                        st.error("❌ Could not locate the just-added record to save VIN.")
                    else:
                        # Vin No is column D
                        worksheet.update(f"D{target_row}", vin_no.strip().upper())
                        st.success("✅ VIN saved successfully.")
                        st.session_state.pending_vin_phone = None
                        st.session_state.pending_vin_row = None
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving VIN: {e}")

with tab_edit:
    st.subheader("Select and Edit Client")
    if df_all.empty:
        st.info("No records to edit.")
    elif not {"Client Name", "Phone"}.issubset(df_all.columns):
        st.error("❌ 'Client Name' or 'Phone' column not found. Please check sheet headers.")
    else:
        # Phone dropdown
        phone_options = sorted(df_all["Phone"].astype(str).dropna().unique().tolist())
        selected_phone = st.selectbox("Select client by phone", [""] + phone_options)

        selected_df = None
        selected_idx = None
        if selected_phone:
            match = df_all[df_all["Phone"].astype(str) == str(selected_phone)]
            if not match.empty:
                selected_df = match.iloc[0]
                selected_idx = match.index[0]

        if selected_df is not None:
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
                        # Preserve current VIN from sheet if present
                        current_vin = str(selected_df.get("Vin No", "")) if "Vin No" in selected_df else ""
                        worksheet.update(f"A{row_index}:D{row_index}", [[date_keep, client_name_e, phone_e, current_vin]])
                        # Prepare VIN Next step after edit
                        st.session_state.pending_vin_phone = phone_e
                        st.session_state.pending_vin_row = row_index
                        st.success("✅ Client updated. Next: update VIN below.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"❌ Error updating client: {e}")

        # VIN Next step (appears after editing)
        if st.session_state.pending_vin_phone and st.session_state.pending_vin_row:
            st.divider()
            st.subheader("Next: Add/Update VIN")
            st.caption(f"For client phone: {st.session_state.pending_vin_phone}")
            # Pre-fill with existing VIN if any
            try:
                df_all_refresh = load_dataframe(worksheet)
                if {"Phone", "Vin No"}.issubset(df_all_refresh.columns):
                    row_now = df_all_refresh[df_all_refresh["Phone"].astype(str) == str(st.session_state.pending_vin_phone)]
                    existing_vin = ""
                    if not row_now.empty:
                        existing_vin = str(row_now.iloc[-1].get("Vin No", "") or "")
                else:
                    existing_vin = ""
            except:
                existing_vin = ""

            with st.form("vin_after_edit_form"):
                vin_no_e = st.text_input("VIN No", value=existing_vin)
                save_vin_e = st.form_submit_button("Save VIN")
            if save_vin_e:
                if vin_no_e.strip() == "":
                    st.error("⚠️ VIN cannot be empty.")
                else:
                    try:
                        target_row = st.session_state.pending_vin_row
                        worksheet.update(f"D{target_row}", vin_no_e.strip().upper())
                        st.success("✅ VIN saved successfully.")
                        st.session_state.pending_vin_phone = None
                        st.session_state.pending_vin_row = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error saving VIN: {e}")
