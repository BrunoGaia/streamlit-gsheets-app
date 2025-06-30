import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

st.title("✅ App de Notas com Google Sheets")

# Interface
nome = st.text_input("Nome:")
turma = st.selectbox("Turma:", ["T1", "T2", "T3", "T4"])
nota = st.slider("Nota:", 0.0, 10.0, 5.0)
nota_tutoria = st.slider("Nota de Tutoria:", 0.0, 10.0, 5.0)

if st.button("Salvar"):
    if nome.strip() == "":
        st.warning("⚠️ O nome é obrigatório.")
    else:
        try:
            # Autenticação com Google Sheets usando secrets
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            gcp_info = st.secrets["gcp_key"]  # ← corrigido
            creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_info, scope)
            client = gspread.authorize(creds)

            # Abre a planilha
            sheet = client.open_by_key("1xK8B8cKWgmt8E2H6QlnASR336ZkTGsVAXX0_Kj9qB0A")
            worksheet = sheet.sheet1

            # Salva os dados
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            linha = [data_hora, nome, turma, nota, nota_tutoria]
            worksheet.append_row(linha)

            st.success("✅ Dados salvos com sucesso!")
        except Exception as e:
            st.error("❌ Erro ao salvar. Verifique as credenciais ou a planilha.")
            st.text(str(e))
