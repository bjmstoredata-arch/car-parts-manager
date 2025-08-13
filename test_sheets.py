import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Expected Google Sheet headers ---
HEADERS = ["Date", "Client Name", "Phone", "Vin No"]

# --- Google Sheets config ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_row_index_for_df_index(df_index: int) -> int:
    """Convert DataFrame index to 1-based row number in Google Sheets (incl. header row)."""
    return int(df_index) + 2

def load_dataframe(worksheet) -> pd.DataFrame:
    """Load all records from the sheet into a DataFrame, strip header whitespace."""
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = [c.strip() for c in df.columns]
    return df

def find_last_row_index_by_phone(worksheet, phone: str) -> int | None:
    """Find the last matching row index (1-based) for a given phone."""
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

# --- Load data ---
try:
    df_all = load_dataframe(worksheet)
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# --- Check headers ---
if list(worksheet.row_values(1)[:len(HEADERS)]) != HEADERS:
    st.info("ℹ️ Make sure your sheet headers (row 1) are exactly: " + " | ".join(HEADERS))

st.title("📑 Client Info")

# --- Session state for VIN step ---
st.session_state.setdefault("pending_vin_phone", None)
st.session_state.setdefault("pending_vin_row", None)

# --- Tabs ---
tab_add, tab_edit = st.tabs(["➕ Add Client", "✏️ Edit Client"])

# =========================================================
# ADD CLIENT TAB
# =========================================================
with tab_add:
    st.subheader("Add New Client")
    submit_add = False  # define variable to avoid NameError

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
                # Append empty VIN for now
                worksheet.append_row([date_str, client_name, phone, ""])
                st.session_state.pending_vin_phone = phone
                st.session_state.pending_vin_row = find_last_row_index_by_phone(worksheet, phone)
                st.success(f"✅ Client saved for phone: {phone}. Next: add VIN below.")
            except Exception as e:
                st.error(f"❌ Error adding client: {e}")

    # --- VIN step after adding ---
    if st.session_state.pending_vin_phone and not submit_add:
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
                    if not target_row:
                        target_row = find_last_row_index_by_phone(worksheet, st.session_state.pending_vin_phone)
                    if not target_row:
                        st.error("❌ Could not locate the record to save VIN.")
                    else:
                        worksheet.update(values=[[vin_no.strip().upper()]], range_name=f"D{target_row}")
                        st.success("✅ VIN saved successfully.")
                        st.session_state.pending_vin_phone = None
                        st.session_state.pending_vin_row = None
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving VIN: {e}")

# =========================================================
# EDIT CLIENT TAB
# =========================================================
with tab_edit:
    st.subheader("Select and Edit Client")
    if df_all.empty:
        st.info("No records to edit.")
    elif not {"Client Name", "Phone"}.issubset(df_all.columns):
        st.error("❌ 'Client Name' or 'Phone' column not found.")
    else:
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
                        current_vin = str(selected_df.get("Vin No", "")) if "Vin No" in selected_df else ""
                        worksheet.update(
                            values=[[date_keep, client_name_e, phone_e, current_vin]],
                            range_name=f"A{row_index}:D{row_index}"
                        )
                        st.session_state.pending_vin_phone = phone_e
                        st.session_state.pending_vin_row = row_index
                        st.success("✅ Client updated. Next: add/update VIN below.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error updating client: {e}")

    # --- VIN step after editing ---
    if st.session_state.pending_vin_phone and st.session_state.pending_vin_row and not submit_add:
        st.divider()
        st.subheader("Next: Add/Update VIN")
        st.caption(f"For client phone: {st.session_state.pending_vin_phone}")

        # Pre-fill VIN if available
        try:
            df_refresh = load_dataframe(worksheet)
            existing_vin = ""
            if {"Phone", "Vin No"}.issubset(df_refresh.columns):
                row_match = df_refresh[df_refresh["Phone"].astype(str) == str(st.session_state.pending_vin_phone)]
                if not row_match.empty:
                    existing_vin = str(row_match.iloc[-1].get("Vin No", "") or "")
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
                    worksheet.update(
                        values=[[vin_no_e.strip().upper()]],
                        range_name=f"D{st.session_state.pending_vin_row}"
                    )
                    st.success("✅ VIN saved successfully.")
                    st.session_state.pending_vin_phone = None
                    st.session_state.pending_vin_row = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving VIN: {e}")
