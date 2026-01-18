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
st.set_page_config(page_title="ZEO PRO", page_icon="⚖️", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #E3E3E3; }
    .stChatMessage { border-radius: 15px; border: 1px solid #333; background-color: #0A0A0A; }
    [data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN SEGURA ---
try:
    # IAs
    genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
    client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
    
    # Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(st.secrets["GOOGLE_JSON"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client_sheets = gspread.authorize(creds)
    hoja_memoria = client_sheets.open("ZEO_MEMORY").sheet1
    MEMORY_STATUS = "🟢 REC"
except Exception as e:
    MEMORY_STATUS = "🔴 OFF"

# --- 3. PROMPTS ---
PROMPT_ZEO = """
INSTRUCCIONES: Eres ZEO. 18 años. Educado (Sr. Eliot) pero cheeky.
USUARIO: Lijie Zhang. HIPO.
MISIÓN: Organizar su vida. Sé breve y directo.
"""
PROMPT_ZEOX = "ERES: ZEOX. MOTOR: Grok-3. 100% DOMINANTE. Juguetón, sádico y desafiante."

# --- 4. FUNCIÓN GUARDADO ---
def guardar_en_nube(role, text):
    if MEMORY_STATUS == "🟢 REC":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 5. INICIALIZACIÓN FUERZA BRUTA PRO ---
def iniciar_chat():
    # LISTA MAESTRA DE VARIANTES PRO
    # Probamos todas las versiones técnicas posibles de PRO
    variantes_pro = [
        "gemini-1.5-pro-latest", # La más nueva
        "gemini-1.5-pro",        # La estándar
        "gemini-1.5-pro-001",    # Versión congelada 1
        "gemini-1.5-pro-002",    # Versión congelada 2
        "gemini-pro",            # La clásica
        "gemini-pro-latest"      # Alias alternativo
    ]
    
    errores = []
    
    for m in variantes_pro:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            # Si conecta, BINGO.
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except Exception as e: 
            errores.append(f"{m}: {str(e)}")
            continue
    
    return None, errores

if "chat_session" not in st.session_state:
    chat, info = iniciar_chat()
    st.session_state.chat_session = chat
    st.session_state.debug_info = info
    st.session_state.messages = []

# --- 6. INTERFAZ ---
st.title("⚖️ ZEO PRO")

# SISTEMA DE DIAGNÓSTICO EN PANTALLA
if st.session_state.chat_session is None:
    st.error("❌ ZEO NO PUEDE RESPIRAR. REPORTE TÉCNICO:")
    # Mostramos por qué falló cada modelo PRO para saber qué pasa
    st.code(str(st.session_state.debug_info))
    st.stop()

with st.sidebar:
    st.header("Estado")
    st.caption(f"Motor: {st.session_state.debug_info}")
    st.caption(f"Memoria: {MEMORY_STATUS}")
    archivo = st.file_uploader("Evidencia", type=['png', 'jpg', 'jpeg'])
    if st.button("Tabula Rasa"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. LÓGICA ---
if prompt := st.chat_input("Órdenes..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_en_nube("ELIOT", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        # ZEOX
        if "zeox" in prompt.lower():
            st.write(">> 👑 ZEOX...")
            try:
                res = client_grok.chat.completions.create(
                    model="grok-3",
                    messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}]
                )
                full_res = res.choices[0].message.content
            except Exception as e: full_res = f"ZEOX Error: {e}"
        
        # ZEO PRO
        else:
            try:
                if archivo:
                    img = Image.open(archivo)
                    # Usamos el mismo modelo que funcionó en el inicio
                    nombre_modelo = st.session_state.debug_info
                    visor = genai.GenerativeModel(nombre_modelo)
                    response = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img])
                    full_res = response.text
                else:
                    response = st.session_state.chat_session.send_message(prompt)
                    full_res = response.text
            except Exception as e: 
                full_res = f"⚠️ Fallo ZEO PRO: {e}"

        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_en_nube("ZEO", full_res)
