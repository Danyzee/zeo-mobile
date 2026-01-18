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

# --- 2. CONEXIÓN BLINDADA ---
try:
    # CEREBRO (Gemini)
    if "CLAVE_GEMINI" in st.secrets:
        genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
    
    # MEMORIA (Excel)
    if "GOOGLE_JSON" in st.secrets:
        # Limpieza preventiva del JSON
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
    # No mostramos el error en pantalla para mantener la interfaz limpia, solo log interno

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

# --- 4. MOTOR DE ARRANQUE (Configurado con SU lista real) ---
def iniciar_motor():
    # Prioridad basada en su lista oficial
    modelos_disponibles = [
        "gemini-2.5-pro",        # La joya de la corona
        "gemini-pro-latest",     # El respaldo estable
        "gemini-3-pro-preview"   # El experimental potente
    ]
    
    for m in modelos_disponibles:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    
    return None, "⚠️ Error: No conecta con modelos 2.5/Pro."

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

# Control de fallo crítico silencioso
if st.session_state.chat_session is None:
    st.error("⚠️ Fallo de conexión. Reinicie la App.")
    st.stop()

with st.sidebar:
    st.header("Panel de Control")
    st.caption(f"Cerebro: {st.session_state.info_motor}")
    st.caption(f"Memoria: {MEMORY_STATUS}")
    archivo = st.file_uploader("Subir evidencia", type=['png', 'jpg', 'jpeg'])
    
    if st.button("Tabula Rasa (Reiniciar)"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# --- 7. CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Órdenes..."):
    # 1. User
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    with st.chat_message("user"): st.markdown(prompt)

    # 2. Assistant
    with st.chat_message("assistant"):
        full_res = "..."
        
        # MODO ZEOX
        if "zeox" in prompt.lower():
            st.write(">> 👑 ZEOX...")
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
                full_res = "⚠️ ZEOX no disponible (Falta clave)."

        # MODO ZEO
        else:
            try:
                if archivo:
                    img = Image.open(archivo)
                    # Usamos el modelo activo (2.5 Pro)
                    visor = genai.GenerativeModel(st.session_state.info_motor)
                    full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                else:
                    full_res = st.session_state.chat_session.send_message(prompt).text
            except Exception as e:
                full_res = f"⚠️ Error ZEO: {e}"
        
        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_log("ZEO", full_res)
