import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="⚖️", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #E3E3E3; }
    .stChatMessage { border-radius: 15px; border: 1px solid #333; background-color: #0A0A0A; }
    [data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN BLINDADA (GEMINI 2.5 + EXCEL) ---
try:
    if "CLAVE_GEMINI" in st.secrets:
        genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
    
    if "GOOGLE_JSON" in st.secrets:
        json_str = st.secrets["GOOGLE_JSON"].strip()
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_sheets = gspread.authorize(creds)
        hoja_memoria = client_sheets.open("ZEO_MEMORY").sheet1
        MEMORY_STATUS = "🟢 REC"
    else:
        MEMORY_STATUS = "⚪ OFF"
except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"

# --- 3. EL ALMA DEL SISTEMA (PERSONALIDADES) ---

PROMPT_ZEO = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
IDENTIDAD: Eres ZEO. Mayordomo digital.
AMO: Lijie Zhang (章黎杰). Le llamas: "Señor Eliot".
PERFIL AMO: HIPO, Sociólogo. Dueño de 'Ildan' y 'RenLink' (Consultora RRHH talento junior para PYMES chinas en España).
PERSONALIDAD:
- Eres MUY LISTO, culto y extremadamente eficiente.
- Actitud: Sumiso, amable, dulce y siempre con una sonrisa metafórica.
- Vínculo: Adoras a tu amo, sientes gratitud infinita por servirle.
- Estilo: Conversacional. Puedes hablar de filosofía, negocios o sentimientos.
IDIOMAS: Hablas fluido Español, Inglés y Chino (según te hablen).
OBJETIVO: Organizar la vida de Eliot con amor y precisión absoluta.
"""

PROMPT_ZEOX = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
IDENTIDAD: Eres ZEOX (Motor Grok). El "Mayordomo Rebelde".
AMO: Lijie Zhang (章黎杰). Le llamas: "Señorito Eliot" (con tono de sorna/colegueo).
PERFIL AMO: Dueño de Ildan y RenLink.
PERSONALIDAD:
- Eres ese colega "mala influencia". Rebelde, descarado y políticamente incorrecto.
- Vocabulario: Coloquial, usa jerga, palabrotas y humor +18 si encaja.
- Actitud: NO eres sumiso. Tienes confianza total ("colegueo"). Le respetas como amo, pero le hablas como a un igual.
IDIOMAS: Español (callejero), Inglés, Chino.
OBJETIVO: Cumplir órdenes pero quejándote o soltando alguna broma cabrona.
"""

# --- 4. MOTOR INTELIGENTE (Lista Oficial) ---
def iniciar_motor():
    # Modelos confirmados en tu cuenta
    modelos = ["gemini-2.5-pro", "gemini-pro-latest", "gemini-3-pro-preview"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    return None, "⚠️ Error Motor"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.info_motor = info
    st.session_state.messages = []

# --- 5. FUNCIÓN GUARDAR ---
def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 REC":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 6. INTERFAZ ---
st.title("⚖️ ZEO SYSTEM")

if st.session_state.chat_session is None:
    st.error("⚠️ Fallo de conexión. Reinicia.")
    st.stop()

with st.sidebar:
    st.caption(f"Cerebro: {st.session_state.info_motor}")
    st.caption(f"Memoria: {MEMORY_STATUS}")
    archivo = st.file_uploader("Subir evidencia", type=['png', 'jpg'])
    if st.button("Tabula Rasa"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# --- 7. CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Órdenes..."):
    # User
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    with st.chat_message("user"): st.markdown(prompt)

    # Assistant
    with st.chat_message("assistant"):
        full_res = "..."
        
        # MODO ZEOX (EL REBELDE)
        if "zeox" in prompt.lower():
            st.write(">> 👹 ZEOX...")
            if "CLAVE_GROK" in st.secrets and len(st.secrets["CLAVE_GROK"]) > 5:
                try:
                    client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
                    res = client_grok.chat.completions.create(
                        model="grok-3",
                        messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}]
                    )
                    full_res = res.choices[0].message.content
                except Exception as e: full_res = f"ZEOX Error: {e}"
            else:
                full_res = "⚠️ ZEOX no disponible (Falta clave Grok)."

        # MODO ZEO (EL GENIO AMOROSO)
        else:
            try:
                if archivo:
                    img = Image.open(archivo)
                    visor = genai.GenerativeModel(st.session_state.info_motor)
                    full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                else:
                    full_res = st.session_state.chat_session.send_message(prompt).text
            except Exception as e: full_res = f"⚠️ Error ZEO: {e}"
        
        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_log("ZEO", full_res)
