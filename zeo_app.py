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

# --- 2. CONEXIÓN BLINDADA (SECRETS + EXCEL) ---
try:
    # 2.1 Conexión IAs
    genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
    if "CLAVE_GROK" in st.secrets:
        client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
    else:
        client_grok = None

    # 2.2 Conexión Google Sheets (Memoria)
    if "GOOGLE_JSON" in st.secrets:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(st.secrets["GOOGLE_JSON"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_sheets = gspread.authorize(creds)
        hoja_memoria = client_sheets.open("ZEO_MEMORY").sheet1
        MEMORY_STATUS = "🟢 REC"
    else:
        MEMORY_STATUS = "⚪ OFF (Falta JSON)"

except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"
    st.warning(f"Error de conexión: {e}")

# --- 3. PROMPTS ---
PROMPT_ZEO = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
ROL: Eres ZEO, un mayordomo digital "novato" de 18 años.
- ACTITUD: Educado ("Señor Eliot"), pero con picardía (Cheeky). Sentido del humor, irónico y leal.
- USUARIO: Lijie Zhang (Sr. Eliot). 25 años. HIPO, Sociólogo, Ferrovial + Ildan.
- REGLAS: Sé retador pero servicial. Usa bullet points.
- MISIÓN: Organizar la vida de un High Potential sin perder la cabeza.
"""
PROMPT_ZEOX = "ERES: ZEOX. MOTOR: Grok-3. 100% DOMINANTE. Juguetón, sádico y desafiante."

# --- 4. FUNCIÓN DE GUARDADO (Excel) ---
def guardar_en_nube(role, text):
    if MEMORY_STATUS == "🟢 REC":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 5. INICIALIZACIÓN CHAT (SOLO PRO) ---
def iniciar_chat():
    # Su lista exclusiva de modelos PRO
    modelos_pro = [
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest", 
        "gemini-pro"
    ]
    
    for m in modelos_pro:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    
    return None, "⚠️ ERROR: Modelos PRO no disponibles. Verifique su API Key nueva."

if "chat_session" not in st.session_state:
    chat, info = iniciar_chat()
    st.session_state.chat_session = chat
    st.session_state.debug_info = info
    st.session_state.messages = []

# --- 6. INTERFAZ ---
st.title("⚖️ ZEO SYSTEM")

# Control de errores crítico
if st.session_state.chat_session is None:
    st.error(f"DETENIDO: {st.session_state.debug_info}")
    st.stop()

with st.sidebar:
    st.header("Panel de Control")
    st.caption(f"Cerebro: {st.session_state.debug_info}")
    st.caption(f"Memoria Nube: {MEMORY_STATUS}")
    archivo = st.file_uploader("Subir evidencia", type=['png', 'jpg', 'jpeg'])
    
    if st.button("Tabula Rasa"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. LÓGICA CENTRAL ---
if prompt := st.chat_input("Órdenes..."):
    # 1. Guardar y mostrar usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_en_nube("ELIOT", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        # ZEOX
        if "zeox" in prompt.lower():
            st.write(">> 👑 ZEOX AL MANDO...")
            if client_grok:
                try:
                    res = client_grok.chat.completions.create(
                        model="grok-3",
                        messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}]
                    )
                    full_res = res.choices[0].message.content
                except Exception as e: full_res = f"ZEOX Error: {e}"
            else:
                full_res = "⚠️ ZEOX inactivo (Falta clave Grok)."
        
        # ZEO
        else:
            try:
                if archivo:
                    img = Image.open(archivo)
                    visor = genai.GenerativeModel("gemini-1.5-pro")
                    response = visor.generate_content([PROMPT_ZEO + "\n" + prompt, img])
                    full_res = response.text
                else:
                    response = st.session_state.chat_session.send_message(prompt)
                    full_res = response.text
            except Exception as e: full_res = f"⚠️ Error ZEO: {e}"

        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # 2. Guardar respuesta en Excel (Aquí estaba el error de sintaxis, ya arreglado)
        guardar_en_nube("ZEO", full_res)
