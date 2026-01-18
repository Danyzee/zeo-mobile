import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="⚖️", layout="centered")
st.markdown("""<style>.stApp { background-color: #000000; color: #E3E3E3; } [data-testid="stHeader"] { display: none; }</style>""", unsafe_allow_html=True)

# --- SISTEMA DE DIAGNÓSTICO ---
debug_logs = []

# --- 1. CONEXIÓN CEREBRO (GEMINI/GROK) ---
try:
    genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
    debug_logs.append("✅ Gemini Key Cargada")
except Exception as e:
    debug_logs.append(f"❌ Error Gemini Key: {e}")

# --- 2. CONEXIÓN MEMORIA (EXCEL) ---
try:
    if "GOOGLE_JSON" in st.secrets:
        # Limpieza de string por si acaso
        json_str = st.secrets["GOOGLE_JSON"].strip()
        if json_str.startswith("'") or json_str.startswith('"'):
             # A veces al copiar se quedan comillas extra al principio/final
             pass 
        
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_sheets = gspread.authorize(creds)
        hoja_memoria = client_sheets.open("ZEO_MEMORY").sheet1
        MEMORY_STATUS = "🟢 REC"
        debug_logs.append("✅ Memoria Excel Conectada")
    else:
        MEMORY_STATUS = "⚪ OFF (Falta JSON)"
except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"
    debug_logs.append(f"❌ Error Excel: {e}")

# --- 3. PROMPTS ---
PROMPT_ZEO = "Eres ZEO. Mayordomo de Lijie Zhang (Sr. Eliot). Organiza su vida. Sé breve, cheeky y leal."

# --- 4. FUNCIÓN GUARDAR ---
def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 REC":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 5. MOTOR DE CHAT ---
def iniciar_motor():
    # Lista de modelos PRO
    modelos = ["gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-pro"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    return None, "SIN CONEXIÓN PRO"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.info_motor = info
    st.session_state.messages = []

# --- 6. INTERFAZ ---
st.title("⚖️ ZEO PRO")

with st.sidebar:
    st.header("Diagnóstico")
    st.code("\n".join(debug_logs), language="text")
    st.caption(f"Motor: {st.session_state.info_motor}")
    st.caption(f"Memoria: {MEMORY_STATUS}")
    
    if st.session_state.chat_session is None:
        st.error("⚠️ EL MOTOR NO ARRANCA. Revisa la Clave Gemini en Secrets.")
    
    archivo = st.file_uploader("Evidencia", type=['png', 'jpg'])
    if st.button("Reiniciar"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# --- 7. BUCLE DE MENSAJES ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Órdenes..."):
    # Guardar User
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    with st.chat_message("user"): st.markdown(prompt)

    # Respuesta Assistant
    with st.chat_message("assistant"):
        full_res = "..."
        if st.session_state.chat_session:
            try:
                if archivo:
                    img = Image.open(archivo)
                    visor = genai.GenerativeModel("gemini-1.5-pro")
                    full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                else:
                    full_res = st.session_state.chat_session.send_message(prompt).text
            except Exception as e:
                full_res = f"⚠️ Error Motor: {e}"
        else:
            full_res = "⚠️ Sistema Apagado (Verifica Secrets)."
        
        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_log("ZEO", full_res)
