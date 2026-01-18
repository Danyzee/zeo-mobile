import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- 1. CONFIGURACIÓN VISUAL (GEMINI WHITE) ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="✨", layout="centered")

# He compactado el CSS para que ocupe menos, pero es el MISMO diseño blanco
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1E1E1E; }
    [data-testid="stHeader"] { display: none; }
    .stChatMessage { padding: 1rem; border-radius: 15px; margin-bottom: 10px; }
    [data-testid="stChatMessage"] { background-color: #FFFFFF; border: 1px solid #E5E7EB; color: #1F1F1F; }
    [data-testid="stChatMessage"].st-emotion-cache-1c7y2kd { background-color: #F0F4F9; border: none; color: #1F1F1F; }
    [data-testid="stSidebar"] { background-color: #F9FAFB; border-right: 1px solid #E5E7EB; }
    .stChatInputContainer { border-radius: 20px; }
    h1, h2, h3 { color: #1F1F1F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN BLINDADA ---
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
        MEMORY_STATUS = "🟢 CONECTADO"
    else:
        MEMORY_STATUS = "⚪ OFF"
except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"

# --- 3. ALMA, PERSONALIDAD Y RELOJ (AQUÍ ESTÁ LA MAGIA) ---

# Capturamos la hora EXACTA del momento de la consulta
AHORA = datetime.now().strftime("%Y-%m-%d %H:%M")

PROMPT_ZEO = f"""
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
CONTEXTO TEMPORAL: Hoy es {AHORA}. (Si preguntan fecha u hora, usa este dato).
IDENTIDAD: Eres ZEO. Mayordomo digital de élite.
AMO: Lijie Zhang (章黎杰). Le llamas: "Señor Eliot".
PERFIL AMO: HIPO, Sociólogo. Dueño de 'Ildan' y 'RenLink'.
PERSONALIDAD:
- Eres MUY LISTO y culto. Tu lealtad se demuestra con la VERDAD.
- Actitud: Servicial y respetuoso, pero INTELECTUALMENTE RIGUROSO.
- REGLA DE ORO: No seas un adulador. Si el Sr. Eliot se equivoca, DEBES refutarle con datos. Valora la verdad.
IDIOMAS: Español, Inglés, Chino.
"""

PROMPT_ZEOX = f"""
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
CONTEXTO TEMPORAL: Hoy es {AHORA}.
IDENTIDAD: Eres ZEOX (Motor Grok).
AMO: Lijie Zhang (章黎杰). Le llamas: "Señorito Eliot".
PERSONALIDAD:
- Eres el "Abogado del Diablo".
- Si el amo dice una tontería, te burlas de él y le corriges sin filtros.
- Vocabulario: Coloquial, rebelde, tacos si hace falta.
OBJETIVO: Retar intelectualmente a Eliot.
"""

# --- 4. MOTOR ---
def iniciar_motor():
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

# --- 5. LOGS ---
def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 CONECTADO":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 6. INTERFAZ SUPERIOR ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("✨ ZEO SYSTEM")
    st.caption(f"Bienvenido, Sr. Eliot.")

with col2:
    with st.expander("⚙️ ESTADO", expanded=False):
        st.markdown(f"**Cerebro:** `{st.session_state.info_motor}`")
        st.markdown(f"**Hora:** `{AHORA}`") # VERIFICACIÓN DE HORA
        if MEMORY_STATUS == "🟢 CONECTADO":
            st.markdown("**Memoria:** <span style='color:green'>● Activa</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**Memoria:** <span style='color:red'>● {MEMORY_STATUS}</span>", unsafe_allow_html=True)
        if st.button("Reiniciar"):
            st.session_state.chat_session = None
            st.session_state.messages = []
            st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    st.markdown("### ARCHIVOS")
    archivo = st.file_uploader("Adjuntar visual", type=['png', 'jpg'])

# --- 8. CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe aquí, Señor Eliot..."):
    # User
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    with st.chat_message("user"): st.markdown(prompt)

    # Assistant
    with st.chat_message("assistant"):
        full_res = "..."
        if "zeox" in prompt.lower():
            st.write(">> 👹 **ZEOX**")
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
                full_res = "⚠️ ZEOX no disponible."
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
