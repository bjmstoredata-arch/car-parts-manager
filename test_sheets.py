if submit_add:
    if phone.strip() == "":
        st.error("⚠️ Phone number is required.")
    else:
        try:
            date_str = datetime.now().strftime("%d/%m/%Y")
            worksheet.append_row([date_str, client_name, phone, ""])  # Empty VIN column for now
            st.session_state["last_added_phone"] = phone
            st.success(f"✅ Client saved for phone: {phone}")
        except Exception as e:
            st.error(f"❌ Error adding client: {e}")

# VIN step after adding
if "last_added_phone" in st.session_state:
    st.info(f"Now enter VIN for client with phone: {st.session_state['last_added_phone']}")
    with st.form("vin_form"):
        vin_no = st.text_input("VIN No")
        submit_vin = st.form_submit_button("Save VIN")
    if submit_vin:
        if vin_no.strip() == "":
            st.error("⚠️ VIN cannot be empty.")
        else:
            try:
                # Find row for this phone
                data = worksheet.get_all_records()
                df_temp = pd.DataFrame(data)
                idx = df_temp.index[df_temp["Phone"] == st.session_state["last_added_phone"]][0]
                row_index = idx + 2  # header offset
                worksheet.update(f"D{row_index}", vin_no.strip().upper())  # Assuming VIN in col D
                st.success("✅ VIN saved successfully.")
                del st.session_state["last_added_phone"]
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving VIN: {e}")
