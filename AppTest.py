import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ------------------- CONFIGURAÇÃO ----------------------
st.set_page_config(page_title="Calculadora de Média - Bruno Gaia", layout="centered")
st.title("📊 Calculadora de Média - Medicina UNIP | Bruno Gaia")

# ------------------- FUNÇÕES AUXILIARES ----------------------
def salvar_dados(nome, turma, notas):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("calcunip-7ca1152065d4.json", scope)
        client = gspread.authorize(creds)
        planilha = client.open_by_key("1STJQ-aaeVf8_aVLC9Q5Qmk7KivmqODlKqeV15KAPSbE")
        aba = planilha.sheet1

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linha = [agora, nome, turma] + [notas[n] for n in ["Tutoria", "Teórica", "Prática", "AEP"]]
        aba.append_row(linha)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar. Verifique a planilha e as credenciais.\n\n{e}")
        return False

def enviar_whatsapp(nome):
    try:
        url = "https://api.z-api.io/instances/3E383630FEE020A6AA2482E7EA6BFAB8/token/F33C05CBAD42BB180092E123/send-text"
        payload = {
            "phone": "551156007770",  # SEU NÚMERO COM DDI+DDD
            "message": f"📢 {nome} acabou de preencher as notas no app!"
        }
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except:
        return False

# ------------------- ABA DE CADASTRO ----------------------
aba1, aba2 = st.tabs(["📝 Cadastrar Notas", "📈 Simular Média"])

with aba1:
    st.markdown("### Informe seus dados e notas")
    nome = st.text_input("Seu nome")
    turma = st.selectbox("Sua turma:", ["T1", "T2", "T3", "T4"])

    pesos = {"Tutoria": 3, "Teórica": 3, "Prática": 2, "AEP": 2}
    notas = {}
    for chave in pesos:
        notas[chave] = st.number_input(f"{chave} (peso {pesos[chave]})", min_value=0.0, max_value=10.0, step=0.1)

    if st.button("Próximo Passo"):
        if nome and turma:
            sucesso = salvar_dados(nome, turma, notas)
            if sucesso:
                enviado = enviar_whatsapp(nome)
                if enviado:
                    st.success("✅ Dados salvos e alerta enviado no WhatsApp!")
                else:
                    st.warning("⚠️ Dados salvos, mas não foi possível enviar alerta via WhatsApp.")
        else:
            st.warning("⚠️ Preencha o nome e a turma.")

# ------------------- ABA DE SIMULAÇÃO ----------------------
with aba2:
    st.markdown("### Simule combinações de notas para atingir média 6.7")
    notas_sim = {}
    for nome in pesos:
        notas_sim[nome] = st.number_input(f"{nome} (peso {pesos[nome]})", min_value=0.0, max_value=10.0, step=0.1, key=f"sim_{nome}")

    pendentes = [k for k in notas_sim if notas_sim[k] == 0.0]

    if len(pendentes) != 2:
        st.info("💡 Deixe exatamente 2 notas zeradas para simular.")
    else:
        slider_nome = pendentes[0]
        calculada_nome = pendentes[1]

        slider_valor = st.slider(f"Nota simulada para {slider_nome}", 0.0, 10.0, 10.0, 0.1)
        notas_sim[slider_nome] = slider_valor

        pontos = {n: notas_sim[n] * pesos[n] / 10 for n in notas_sim}
        total = sum(pontos.values())
        faltando = round(6.7 - total, 3)

        if faltando < 0 or faltando > pesos[calculada_nome]:
            st.error("❌ Sem solução com essa combinação. Tente outro valor no slider.")
        else:
            nota_calc = round((faltando * 10) / pesos[calculada_nome], 2)
            notas_sim[calculada_nome] = nota_calc
            st.success(f"✅ Para atingir média 6.7, você precisa tirar {nota_calc} em {calculada_nome}.")

            df_resultado = pd.DataFrame(list(notas_sim.items()), columns=["Avaliação", "Nota"])
            st.dataframe(df_resultado, use_container_width=True)

            # Combinações possíveis
            combinacoes = []
            for x in np.arange(0, 10.1, 0.1):
                for y in np.arange(0, 10.1, 0.1):
                    temp = notas_sim.copy()
                    temp[slider_nome] = round(x, 1)
                    temp[calculada_nome] = round(y, 1)
                    pontos_temp = {n: temp[n] * pesos[n] / 10 for n in temp}
                    if abs(sum(pontos_temp.values()) - 6.7) < 0.01:
                        combinacoes.append({slider_nome: x, calculada_nome: y})

            if combinacoes:
                df_combos = pd.DataFrame(combinacoes).drop_duplicates().sort_values(by=slider_nome, ascending=False)
                st.markdown("### 📋 Combinações possíveis:")
                st.dataframe(df_combos, use_container_width=True)

                fig, ax = plt.subplots()
                x_vals = [c[slider_nome] for c in combinacoes]
                y_vals = [c[calculada_nome] for c in combinacoes]
                ax.scatter(x_vals, y_vals, color='blue', s=10)
                ax.set_xlim(0, 10)
                ax.set_ylim(0, 10)
                ax.set_xticks(np.arange(0, 10.5, 1.0))
                ax.set_yticks(np.arange(0, 10.5, 1.0))
                ax.set_xticks(np.arange(0, 10.5, 0.5), minor=True)
                ax.set_yticks(np.arange(0, 10.5, 0.5), minor=True)
                ax.grid(True, which='major', linestyle='--')
                ax.grid(True, which='minor', linestyle=':', linewidth=0.5)
                ax.set_xlabel(slider_nome)
                ax.set_ylabel(calculada_nome)
                ax.set_title("🔵 Combinações para média 6.7")
                st.pyplot(fig)
            else:
                st.error("❌ Nenhuma combinação encontrada.")

