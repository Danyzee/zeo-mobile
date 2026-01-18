import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="⚖️", layout="centered")
st.markdown("""<style>.stApp { background-color: #000000; color: #E3E3E3; } [data-testid="stHeader"] { display: none; }</style>""", unsafe_allow_html=True)

st.title("⚖️ ZEO PRO")

# --- SISTEMA DE DIAGNÓSTICO (AHORA VISIBLE AL CENTRO) ---
debug_logs = []
motor_status = "❌ OFF"

# 1. VERIFICACIÓN DE LIBRERÍAS
try:
    import google.generativeai as test_lib
    version = test_lib.__version__
    debug_logs.append(f"ℹ️ Versión Librería Google: {version}")
except:
    debug_logs.append("⚠️ No se puede leer la versión de la librería")

# 2. CONEXIÓN CEREBRO
try:
    if "CLAVE_GEMINI" in st.secrets:
        clave = st.secrets["CLAVE_GEMINI"]
        if clave.startswith('"') or " " in clave:
            debug_logs.append("❌ ERROR CRÍTICO: La clave en Secrets tiene comillas o espacios extra.")
        else:
            genai.configure(api_key=clave)
            debug_logs.append("✅ Clave Gemini detectada")
            motor_status = "✅ ON"
    else:
        debug_logs.append("❌ ERROR: No existe 'CLAVE_GEMINI' en Secrets.")
except Exception as e:
    debug_logs.append(f"❌ Error al configurar Key: {e}")

# 3. CONEXIÓN MEMORIA
try:
    if "GOOGLE_JSON" in st.secrets:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(st.secrets["GOOGLE_JSON"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_sheets = gspread.authorize(creds)
        hoja_memoria = client_sheets.open("ZEO_MEMORY").sheet1
        MEMORY_STATUS = "🟢 REC"
        debug_logs.append("✅ Memoria Excel Conectada")
    else:
        MEMORY_STATUS = "⚪ OFF (Falta JSON)"
        debug_logs.append("ℹ️ Sin memoria Excel (JSON no configurado)")
except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"
    debug_logs.append(f"❌ Error Excel: {e}")

# --- MOSTRAR DIAGNÓSTICO EN PANTALLA ---
with st.expander("🛠️ VER ESTADO DEL SISTEMA (Click aquí)", expanded=True):
    st.write(f"Estado Motor: {motor_status}")
    st.code("\n".join(debug_logs), language="text")

# --- MOTOR DE CHAT ---
def iniciar_motor():
    modelos = ["gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-pro"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": ["Eres ZEO. Mayordomo. Sé breve."]}]), m
        except: continue
    return None, "SIN CONEXIÓN PRO"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.messages = []

# --- INTERFAZ DE CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Órdenes..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    if MEMORY_STATUS == "🟢 REC":
        try: hoja_memoria.append_row([str(datetime.now()), "ELIOT", prompt])
        except: pass
    
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if st.session_state.chat_session:
            try:
                res = st.session_state.chat_session.send_message(prompt).text
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                if MEMORY_STATUS == "🟢 REC":
                    try: hoja_memoria.append_row([str(datetime.now()), "ZEO", res])
                    except: pass
            except Exception as e: st.error(f"Error: {e}")
        else:
            st.error("⚠️ SISTEMA APAGADO: Revisa el diagnóstico arriba.")
