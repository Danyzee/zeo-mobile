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

st.title("⚖️ ZEO PRO - DIAGNÓSTICO")

# --- VARIABLES GLOBALES ---
debug_logs = []
error_detalle = ""

# 1. CONFIGURAR LLAVE
try:
    if "CLAVE_GEMINI" in st.secrets:
        genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
        debug_logs.append("✅ Key Configurada")
    else:
        debug_logs.append("❌ Falta CLAVE_GEMINI en Secrets")
except Exception as e:
    debug_logs.append(f"❌ Error Config: {e}")

# 2. CONEXIÓN EXCEL
try:
    if "GOOGLE_JSON" in st.secrets:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(st.secrets["GOOGLE_JSON"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_sheets = gspread.authorize(creds)
        hoja_memoria = client_sheets.open("ZEO_MEMORY").sheet1
        MEMORY_STATUS = "🟢 REC"
    else:
        MEMORY_STATUS = "⚪ OFF"
except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"

# --- MOTOR DE ARRANQUE (AQUÍ ESTÁ EL CHIVATO) ---
def iniciar_motor():
    global error_detalle
    # Probamos SOLO el modelo más estable para ver el error real
    modelo_prueba = "gemini-1.5-pro"
    
    try:
        debug_logs.append(f"🔌 Intentando conectar con {modelo_prueba}...")
        test = genai.GenerativeModel(modelo_prueba)
        # Intentamos generar un 'hola' simple
        response = test.generate_content("ping")
        debug_logs.append("✅ ¡CONEXIÓN EXITOSA!")
        return test.start_chat(history=[{"role": "user", "parts": ["Eres ZEO."]}]), modelo_prueba
    except Exception as e:
        # AQUÍ CAPTURAMOS EL ERROR REAL
        error_real = str(e)
        debug_logs.append(f"❌ FALLO MOTOR: {error_real}")
        error_detalle = error_real
        return None, "FALLO CRÍTICO"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.messages = []

# --- MOSTRAR EL ERROR EN GRANDE ---
if st.session_state.chat_session is None:
    st.error("⚠️ EL MOTOR NO ARRANCA. LEE EL ERROR ABAJO:")
    st.code(error_detalle, language="text") # ESTO ES LO QUE NECESITO QUE LEAS
    st.warning("Copia el mensaje rojo de arriba y pégalo en el chat.")

# --- DIAGNÓSTICO VISUAL ---
with st.expander("🛠️ LOGS DEL SISTEMA", expanded=True):
    st.write(f"Memoria: {MEMORY_STATUS}")
    st.text("\n".join(debug_logs))

# --- INTERFAZ BÁSICA ---
if prompt := st.chat_input("Escribe para probar..."):
    st.write("El sistema está detenido. Revisa el error arriba.")
