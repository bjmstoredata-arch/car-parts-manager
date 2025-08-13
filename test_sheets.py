import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Expected headers (order used for append/update) ---
HEADERS = [
    "Date", "Client Name", "Phone", "Vin No", "Model",
    "Prod. Yr", "Body", "Engine", "Code", "Transmission"
]

# --- Google Sheets Configuration ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def normalize_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # strip spaces
    df.columns = [c.strip() for c in df.columns]
    # build synonym map (case-insensitive)
    syn = {
        "date": "Date", "fecha": "Date",
        "client name": "Client Name", "cliente": "Client Name", "name": "Client Name",
        "phone": "Phone", "phone number": "Phone", "telefono": "Phone", "tel": "Phone",
        "mobile": "Phone", "cel": "Phone", "celular": "Phone",
        "vin no": "Vin No", "vin": "Vin No", "vin number": "Vin No",
        "model": "Model", "modelo": "Model",
        "prod. yr": "Prod. Yr", "prod yr": "Prod. Yr", "production year": "Prod. Yr",
        "year": "Prod. Yr", "año": "Prod. Yr", "anio": "Prod. Yr",
        "body": "Body", "carroceria": "Body", "carrocería": "Body",
        "engine": "Engine", "motor": "Engine",
        "code": "Code", "codigo": "Code", "código": "Code",
        "transmission": "Transmission", "transmision": "Transmission", "transmisión": "Transmission",
    }
    rename_map = {}
    for c in df.columns:
        key = c.strip().lower()
        if key in syn:
            rename_map[c] = syn[key]
    df = df.rename(columns=rename_map)
    return df

def get_row_index_for_df_index(df_index: int) -> int:
    # gspread rows start at 1, row 1 is headers, so add 2
    return int(df_index) + 2

try:
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=SCOPE
    )
    client = gspread.authorize(creds)
    SHEET_NAME = "CarPartsDatabase"  # change if needed
    worksheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"❌ Could not connect to Google Sheets: {e}")
    st.stop()

# --- Load data ---
try:
    data = worksheet.get_all_records()
    df_all = pd.DataFrame(data)
    df_all = normalize_and_rename_columns(df_all)
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

st.title("📑 Cliente Info")

# --- Search by Phone (only) ---
st.subheader("🔍 Search by Phone Number")
search_phone = st.text_input("Enter phone number to search")
df_view = df_all.copy()
if search_phone:
    if "Phone" in df_view.columns:
        df_view["Phone"] = df_view["Phone"].astype(str).fillna("")
        df_view = df_view[df_view["Phone"].str.contains(search_phone, case=False, na=False)]
    else:
        st.warning("⚠️ 'Phone' column not found. Check your sheet headers.")

# --- Show table ---
if not df_view.empty:
    st.subheader("📋 Records")
    st.dataframe(df_view)
else:
    st.info("No matching records found.")

# --- Add a new record (only Phone required) ---
st.subheader("➕ Add a New Record")
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
            row = [
                date_str, client_name, phone, vin_no_upper, model,
                prod_yr, body, engine, code, transmission
            ]
            # Optional: basic header check to prevent misalignment
            if not set(["Phone"]).issubset(set(df_all.columns)):
                st.warning("⚠️ Your sheet may not have the expected headers. Expected at least: Phone.")
            worksheet.append_row(row)
            st.success(f"✅ Record saved for phone: {phone}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error adding record: {e}")

# --- Edit an existing record ---
st.subheader("✏️ Edit Client")
if df_all.empty:
    st.info("No records to edit yet.")
else:
    if "Phone" not in df_all.columns:
        st.error("❌ 'Phone' column not found. Please confirm your sheet headers match expected names.")
    else:
        # Build phone options
        phone_options = sorted(pd.Series(df_all["Phone"].astype(str)).dropna().unique().tolist())
        selected_phone = st.selectbox("Select client by phone", [""] + phone_options)

        selected_df = None
        selected_df_index = None

        if selected_phone:
            matches = df_all[df_all["Phone"].astype(str) == str(selected_phone)]
            if matches.empty:
                st.warning("No record found for that phone (headers or data might be off).")
            elif len(matches) == 1:
                selected_df = matches.iloc[0]
                selected_df_index = matches.index[0]
            else:
                # Multiple entries for same phone: disambiguate
                labels = []
                idx_map = {}
                for i, (idx, row) in enumerate(matches.iterrows(), start=1):
                    label = f"{i}: {row.get('Date','')} | {row.get('Client Name','')} | VIN {row.get('Vin No','')}"
                    labels.append(label)
                    idx_map[label] = idx
                choice = st.selectbox("Multiple records found. Choose one:", labels)
                if choice:
                    selected_df_index = idx_map[choice]
                    selected_df = df_all.loc[selected_df_index]

        if selected_df is not None and selected_df_index is not None:
            with st.form("edit_form"):
                client_name_e = st.text_input("Client Name", value=str(selected_df.get("Client Name", "")))
                phone_e = st.text_input("Phone", value=str(selected_df.get("Phone", "")))
                vin_no_e = st.text_input("Vin No", value=str(selected_df.get("Vin No", "")))
                model_e = st.text_input("Model", value=str(selected_df.get("Model", "")))
                prod_yr_e = st.text_input("Prod. Yr", value=str(selected_df.get("Prod. Yr", "")))
                body_e = st.text_input("Body", value=str(selected_df.get("Body", "")))
                engine_e = st.text_input("Engine", value=str(selected_df.get("Engine", "")))
                code_e = st.text_input("Code", value=str(selected_df.get("Code", "")))
                transmission_e = st.text_input("Transmission", value=str(selected_df.get("Transmission", "")))
                save_changes = st.form_submit_button("Save Changes")

            if save_changes:
                if phone_e.strip() == "":
                    st.error("⚠️ Phone number is required.")
                else:
                    try:
                        row_index = get_row_index_for_df_index(selected_df_index)
                        vin_no_e_up = vin_no_e.strip().upper() if vin_no_e else ""
                        # Keep original Date unless you want to refresh it
                        date_keep = str(selected_df.get("Date", ""))
                        values = [
                            date_keep, client_name_e, phone_e, vin_no_e_up, model_e,
                            prod_yr_e, body_e, engine_e, code_e, transmission_e
                        ]
                        # Update the row across expected columns A:J
                        worksheet.update(f"A{row_index}:J{row_index}", [values])
                        st.success("✅ Client record updated successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error updating record: {e}")

# --- Gentle nudge if headers are off ---
if not df_all.empty:
    missing = [h for h in HEADERS if h not in df_all.columns]
    if missing:
        st.info("ℹ️ Tip: For best results, use these headers exactly in row 1: "
                + " | ".join(HEADERS))
