%%writefile app.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.title("✅ Streamlit + Google Sheets (sem senha)")

nome = st.text_input("Nome:")
nota = st.slider("Nota:", 0.0, 10.0, 5.0)

if st.button("Salvar"):
    if nome.strip() == "":
        st.warning("⚠️ Nome obrigatório.")
    else:
        try:
            scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_key("1xK8B8cKWgmt8E2H6QlnASR336ZkTGsVAXX0_Kj9qB0A")
            worksheet = sheet.sheet1
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([data_hora, nome, nota])
            st.success("✅ Dados salvos com sucesso!")
        except Exception as e:
            st.error("❌ Erro ao salvar.")
            print("Erro:", e)
