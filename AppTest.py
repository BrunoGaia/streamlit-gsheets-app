# streamlit_med_unip.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import requests

def enviar_whatsapp(nome):
    try:
        payload = {
            "phone": st.secrets["telefone_destino"],
            "message": f"📩 {nome} acabou de registrar as notas no app da UNIP!"
        }
        url = st.secrets["whatsapp_api_url"]
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.toast("✅ Notificação enviada via WhatsApp.")
        else:
            st.warning("⚠️ Falha ao enviar WhatsApp.")
            st.text(f"Código de status: {response.status_code}")
    except Exception as e:
        st.warning("⚠️ Erro ao enviar WhatsApp.")
        st.text(str(e))
st.set_page_config(page_title="UNIP - Cadastro e Simulador de Notas", layout="wide")

if "etapa" not in st.session_state:
    st.session_state.etapa = "cadastro"

if "notas_salvas" not in st.session_state:
    st.session_state.notas_salvas = {}

menu = st.sidebar.radio("Escolha uma aba:", ["📥 Cadastrar Notas", "🧮 Simular Média"])

# ---------------------------
# ABA 1: CADASTRO
# ---------------------------
if menu == "📥 Cadastrar Notas":
    st.title("📥 Cadastro de Notas - Medicina UNIP")

    nome = st.text_input("Nome:")
    turma = st.selectbox("Turma:", ["T1", "T2", "T3", "T4"])
    notas = {}
    pesos = {"Tutoria": 3, "Teórica": 3, "Prática": 2, "AEP": 2}

    st.markdown("### 📝 Digite suas 4 notas (deixe duas como 0 se ainda não tiver):")
    for key in pesos:
        notas[key] = st.number_input(f"{key} (peso {pesos[key]})", min_value=0.0, max_value=10.0, step=0.1, key=key+"_cad")

    if st.button("Próximo Passo"):
        if nome.strip() == "":
            st.warning("⚠️ Preencha o nome.")
        elif list(notas.values()).count(0.0) != 2:
            st.warning("⚠️ Deixe exatamente 2 notas com 0.0 para continuar.")
        else:
            try:
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                gcp_info = st.secrets["gcp_key"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_info, scope)
                client = gspread.authorize(creds)
                sheet = client.open_by_key("1xK8B8cKWgmt8E2H6QlnASR336ZkTGsVAXX0_Kj9qB0A")
                worksheet = sheet.sheet1
                data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                linha = [data_hora, nome, turma, notas["Tutoria"], notas["Teórica"], notas["Prática"], notas["AEP"]]
                worksheet.append_row(linha)
                st.success("✅ Notas salvas com sucesso! Agora vá para a aba \"Simular Média\" para continuar.")
                enviar_whatsapp(nome)
                st.session_state.etapa = "simulador"
                st.session_state.notas_salvas = notas

                # Média do último dia
                records = worksheet.get_all_records()
                df = pd.DataFrame(records)
                df['Data'] = pd.to_datetime(df['Data/Hora']).dt.date
                hoje = datetime.now().date()
                df_hoje = df[df['Data'] == hoje].copy()
                df_hoje = df_hoje[(df_hoje[['Tutoria', 'Teórica', 'Prática', 'AEP']] != 0).any(axis=1)]

                if not df_hoje.empty:
                    medias_colunas = df_hoje[['Tutoria', 'Teórica', 'Prática', 'AEP']].replace(0, np.nan).mean()
                    for col, valor in medias_colunas.items():
                        st.info(f"📌 Média de {col} hoje : **{valor:.2f}**")
                    st.info(f"👥 Número de usuários que preencheram hoje: **{df_hoje.shape[0]}**")

            except Exception as e:
                st.error("❌ Erro ao salvar. Verifique a planilha e as credenciais.")
                st.text(str(e))

# ---------------------------
# ABA 2: SIMULADOR
# ---------------------------
elif menu == "🧮 Simular Média":
    if st.session_state.etapa != "simulador" or not st.session_state.notas_salvas:
        st.warning("⚠️ Preencha e salve as notas na aba \"Cadastrar Notas\" antes de acessar o simulador.")
    else:
        st.title("🧮 Simulador de Média - Medicina UNIP")

        pesos = {"Tutoria": 3, "Teórica": 3, "Prática": 2, "AEP": 2}
        notas = st.session_state.notas_salvas.copy()

        pendentes = [k for k in notas if notas[k] == 0.0]

        if len(pendentes) != 2:
            st.warning("⚠️ Deixe exatamente **2 avaliações com nota 0** para ativar o cálculo.")
        else:
            st.markdown("### 🔄 Simulando todas as combinações possíveis")
            combinacoes = []
            for x in np.arange(0, 10.1, 0.1):
                for y in np.arange(0, 10.1, 0.1):
                    temp = notas.copy()
                    temp[pendentes[0]] = round(x, 1)
                    temp[pendentes[1]] = round(y, 1)
                    pontos_temp = {n: temp[n] * pesos[n] / 10 for n in temp}
                    if abs(sum(pontos_temp.values()) - 6.7) < 0.01:
                        combinacoes.append({pendentes[0]: x, pendentes[1]: y})

            if combinacoes:
                df_combos = pd.DataFrame(combinacoes).drop_duplicates().sort_values(by=pendentes[0], ascending=False)
                st.markdown(f"### 🧮 Todas as {len(df_combos)} combinações possíveis:")
                st.dataframe(df_combos, use_container_width=True)

                x_vals = [c[pendentes[0]] for c in combinacoes]
                y_vals = [c[pendentes[1]] for c in combinacoes]
                fig, ax = plt.subplots()
                ax.scatter(x_vals, y_vals, color='blue', s=10)
                ax.set_xlim(0, 10)
                ax.set_ylim(0, 10)
                ax.set_xticks(np.arange(0, 10.5, 1.0))
                ax.set_yticks(np.arange(0, 10.5, 1.0))
                ax.set_xticks(np.arange(0, 10.5, 0.5), minor=True)
                ax.set_yticks(np.arange(0, 10.5, 0.5), minor=True)
                ax.grid(True, which='major', linestyle='--')
                ax.grid(True, which='minor', linestyle=':', linewidth=0.5)
                ax.set_xlabel(pendentes[0])
                ax.set_ylabel(pendentes[1])
                ax.set_title("🔵 Combinações para média 6.7")
                st.pyplot(fig)
            else:
                st.error("❌ Nenhuma combinação encontrada para média 6.7 com essas avaliações pendentes.")

st.markdown("---")
st.caption("Desenvolvido por Bruno Gaia · Medicina UNIP · 2025")

