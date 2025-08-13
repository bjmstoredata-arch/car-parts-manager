import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ============================================================================
# Google Sheets configuration
# ============================================================================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_HEADERS = ["Date", "Client Name", "Phone"]
VIN_HEADERS = ["Phone", "VIN No", "Date Added"]
SPREADSHEET_NAME = "CarPartsDatabase"
CLIENT_SHEET_NAME = "Clients"
VIN_SHEET_NAME = "VinRecords"

# ============================================================================
# Helpers
# ============================================================================
def connect_sheets():
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=SCOPE
    )
    gc = gspread.authorize(creds)
    sh = gc.open(SPREADSHEET_NAME)
    return sh.worksheet(CLIENT_SHEET_NAME), sh.worksheet(VIN_SHEET_NAME)

def load_df(sheet) -> pd.DataFrame:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df.columns = [c.strip() for c in df.columns]
    return df

def ensure_headers(sheet, expected_headers):
    values = sheet.get_all_values()
    if not values:
        sheet.append_row(expected_headers)

def append_client(client_ws, name, phone):
    date_str = datetime.now().strftime("%d/%m/%Y")
    client_ws.append_row([date_str, name, phone])

def update_client_row(client_ws, df_clients, idx, name, phone):
    row_number = idx + 2
    date_keep = df_clients.loc[idx, "Date"] if "Date" in df_clients.columns else ""
    client_ws.update(
        values=[[date_keep, name, phone]],
        range_name=f"A{row_number}:C{row_number}"
    )
    return row_number

def append_vin(vin_ws, phone, vin_no):
    date_added = datetime.now().strftime("%d/%m/%Y")
    vin_ws.append_row([str(phone), vin_no.strip().upper(), date_added])

# ============================================================================
# Connect and load
# ============================================================================
try:
    client_ws, vin_ws = connect_sheets()
    ensure_headers(client_ws, CLIENT_HEADERS)
    ensure_headers(vin_ws, VIN_HEADERS)
    df_clients = load_df(client_ws)
    df_vins = load_df(vin_ws)
except Exception as e:
    st.error(f"❌ Error loading Google Sheets: {e}")
    st.stop()

# ============================================================================
# App UI
# ============================================================================
st.title("📑 Client Info")

# Session state
st.session_state.setdefault("selected_phone", "")
st.session_state.setdefault("active_tab", "➕ Add Client")

tab_options = ["➕ Add Client", "✏️ Edit Client", "🚗 VINs"]
tab_index = tab_options.index(st.session_state.active_tab)
tab_choice = st.radio("Select section", tab_options, index=tab_index)

# ----------------------------------------------------------------------------
# Add Client
# ----------------------------------------------------------------------------
if tab_choice == "➕ Add Client":
    st.subheader("Add new client")
    with st.form("form_add_client"):
        client_name = st.text_input("Client Name")
        phone = st.text_input("Phone")
        add_client_btn = st.form_submit_button("Add Client")

    if add_client_btn:
        if phone.strip() == "":
            st.error("⚠️ Phone number is required.")
        else:
            try:
                append_client(client_ws, client_name, phone)
                st.success(f"✅ Client added: {phone}")
                st.session_state.selected_phone = phone
                st.session_state.active_tab = "🚗 VINs"
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error adding client: {e}")

# ----------------------------------------------------------------------------
# Edit Client
# ----------------------------------------------------------------------------
elif tab_choice == "✏️ Edit Client":
    st.subheader("Edit client")
    phone_list = sorted(df_clients["Phone"].dropna().astype(str).unique().tolist()) if not df_clients.empty else []
    selected_phone_edit = st.selectbox(
        "Select client by phone",
        [""] + phone_list,
        key="edit_client_select"
    )

    if selected_phone_edit:
        match = df_clients[df_clients["Phone"].astype(str) == selected_phone_edit]
        if not match.empty:
            row = match.iloc[-1]
            idx = match.index[-1]

            with st.form("form_edit_client"):
                client_name_e = st.text_input("Client Name", row.get("Client Name", ""))
                phone_e = st.text_input("Phone", row.get("Phone", ""))
                save_edit_btn = st.form_submit_button("Save Changes")

            if save_edit_btn:
                if phone_e.strip() == "":
                    st.error("⚠️ Phone number is required.")
                else:
                    try:
                        update_client_row(client_ws, df_clients, idx, client_name_e, phone_e)
                        st.success("✅ Client updated")
                        st.session_state.selected_phone = phone_e
                        st.session_state.active_tab = "🚗 VINs"
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error updating client: {e}")

# ----------------------------------------------------------------------------
# VINs
# ----------------------------------------------------------------------------
elif tab_choice == "🚗 VINs":
    st.subheader("VINs")

    phone_choices = sorted(df_clients["Phone"].dropna().astype(str).unique().tolist()) if not df_clients.empty else []
    default_index = 0
    if st.session_state.selected_phone and st.session_state.selected_phone in phone_choices:
        default_index = phone_choices.index(st.session_state.selected_phone) + 1

    selected_phone_vins = st.selectbox(
        "Select client by phone",
        [""] + phone_choices,
        index=default_index,
        key="vin_client_select"
    )

    if selected_phone_vins:
        st.session_state.selected_phone = selected_phone_vins
        df_client_vins = df_vins[df_vins["Phone"].astype(str) == selected_phone_vins] if not df_vins.empty else pd.DataFrame()
        st.markdown(f"**VINs for {selected_phone_vins}:**")
        if not df_client_vins.empty:
            st.dataframe(df_client_vins.sort_values(by="Date Added", ascending=False), use_container_width=True)
        else:
            st.info("No VINs found for this client.")

        with st.form("form_add_vin"):
            vin_new = st.text_input("Add new VIN")
            save_vin_btn = st.form_submit_button("Save VIN")

        if save_vin_btn:
            if vin_new.strip() == "":
                st.error("⚠️ VIN cannot be empty.")
            else:
                try:
                    append_vin(vin_ws, selected_phone_vins, vin_new)
                    st.success("✅ VIN saved")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving VIN: {e}")
    else:
        st.info("Select a client phone to view and add VINs.")
