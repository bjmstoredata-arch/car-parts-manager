import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

HEADERS = [
    "Date", "Client Name", "Phone", "Vin No", "Model",
    "Prod. Yr", "Body", "Engine", "Code", "Transmission"
]

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def normalize_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df.columns = [c.strip() for c in df.columns]
    syn = {
        "date": "Date", "client name": "Client Name", "phone": "Phone",
        "vin no": "Vin No", "vin": "Vin No",
        "model": "Model", "prod. yr": "Prod. Yr", "body": "Body",
        "engine": "Engine", "code": "Code", "transmission": "Transmission"
    }
    rename_map = {c: syn[c.lower()] for c in df.columns if c.lower() in syn}
    df = df.rename(columns=rename_map)
    return df

def get_row_index_for_df_index(df_index: int) -> int:
    return int(df_index) + 2

# --- Conexión Google Sheets ---
try:
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=SCOPE
    )
    client = gspread.authorize(creds)
    SHEET_NAME = "CarPartsDatabase"
    worksheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"❌ Could not connect to Google Sheets: {e}")
    st.stop()

# --- Cargar datos ---
try:
    data = worksheet.get_all_records()
    df_all = normalize_and_rename_columns(pd.DataFrame(data))
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

st.title("📑 Cliente Info")

# --- Tabs ---
tab_add, tab_edit = st.tabs(["➕ Add Client", "✏️ Edit Client"])

with tab_add:
    st.subheader("Agregar nuevo cliente")
    with st.form("add_record_form"):
        client_name = st.text_input("Client Name")
        phone = st.text_input("Phone")
        vin_no = st.text_input("Vin No")
        model = st.text_input("Model")
        prod_yr = st.text_input("Prod. Yr")
        body = st.text_input("Body")
        engine = st.text_input("Engine")
        code = st.text_input("Code")
        transmission = st.text_input("Transmission")
        submit_add = st.form_submit_button("Add")

    if submit_add:
        if phone.strip() == "":
            st.error("⚠️ Phone number is required.")
        else:
            try:
                date_str = datetime.now().strftime("%d/%m/%Y")
                vin_no_upper = vin_no.strip().upper() if vin_no else ""
                worksheet.append_row([
                    date_str, client_name, phone, vin_no_upper, model,
                    prod_yr, body, engine, code, transmission
                ])
                st.success(f"✅ Record saved for phone: {phone}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error adding record: {e}")

with tab_edit:
    st.subheader("Buscar y editar cliente")
    if df_all.empty:
        st.info("No records to edit yet.")
    elif "Phone" not in df_all.columns:
        st.error("❌ 'Phone' column not found. Please check headers.")
    else:
        phone_options = sorted(df_all["Phone"].astype(str).dropna().unique().tolist())
        selected_phone = st.selectbox("Select client by phone", [""] + phone_options)

        if selected_phone:
            matches = df_all[df_all["Phone"].astype(str) == str(selected_phone)]
            if not matches.empty:
                selected_df = matches.iloc[0]
                selected_df_index = matches.index[0]

                with st.form("edit_form"):
                    client_name_e = st.text_input("Client Name", str(selected_df.get("Client Name", "")))
                    phone_e = st.text_input("Phone", str(selected_df.get("Phone", "")))
                    vin_no_e = st.text_input("Vin No", str(selected_df.get("Vin No", "")))
                    model_e = st.text_input("Model", str(selected_df.get("Model", "")))
                    prod_yr_e = st.text_input("Prod. Yr", str(selected_df.get("Prod. Yr", "")))
                    body_e = st.text_input("Body", str(selected_df.get("Body", "")))
                    engine_e = st.text_input("Engine", str(selected_df.get("Engine", "")))
                    code_e = st.text_input("Code", str(selected_df.get("Code", "")))
                    transmission_e = st.text_input("Transmission", str(selected_df.get("Transmission", "")))
                    save_changes = st.form_submit_button("Save Changes")

                if save_changes:
                    if phone_e.strip() == "":
                        st.error("⚠️ Phone number is required.")
                    else:
                        try:
                            row_index = get_row_index_for_df_index(selected_df_index)
                            vin_no_e_up = vin_no_e.strip().upper() if vin_no_e else ""
                            date_keep = str(selected_df.get("Date", ""))
                            values = [
                                date_keep, client_name_e, phone_e, vin_no_e_up, model_e,
                                prod_yr_e, body_e, engine_e, code_e, transmission_e
                            ]
                            worksheet.update(f"A{row_index}:J{row_index}", [values])
                            st.success("✅ Client record updated successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error updating record: {e}")
