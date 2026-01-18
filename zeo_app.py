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

# --- VARIABLES GLOBALES ---
debug_logs = []
modelo_activo = "BUSCANDO..."

# 1. CONFIGURAR LLAVE
try:
    if "CLAVE_GEMINI" in st.secrets:
        genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
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

# --- 3. PROMPTS ---
PROMPT_ZEO = "Eres ZEO. Mayordomo de Lijie Zhang (Sr. Eliot). Organiza su vida. Sé breve, cheeky y leal."
PROMPT_ZEOX = "ERES: ZEOX. MOTOR: Grok-3. 100% DOMINANTE. Juguetón, sádico y desafiante."

# --- 4. MOTOR INTELIGENTE (EL CAZADOR) ---
def iniciar_motor():
    global modelo_activo
    # LISTA DE VARIANTES PRO (Probará una por una)
    variantes = [
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro-001",
        "gemini-1.5-pro-002",
        "gemini-pro"
    ]
    
    errores = []
    
    for m in variantes:
        try:
            # Prueba de conexión
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            # Si pasa el ping, es el elegido
            modelo_activo = m
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except Exception as e:
            errores.append(f"{m}: {str(e)}")
            continue
            
    return None, f"NINGUNO RESPONDE. Errores: {errores}"

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
# Mostrar qué modelo ganó la carrera
if st.session_state.chat_session:
    st.caption(f"🟢 SISTEMA ONLINE | Motor: {st.session_state.info_motor} | Memoria: {MEMORY_STATUS}")
else:
    st.error("⚠️ EL MOTOR NO ARRANCA")
    with st.expander("Ver Errores Técnicos"):
        st.write(st.session_state.info_motor)

with st.sidebar:
    st.header("Panel de Control")
    archivo = st.file_uploader("Subir evidencia", type=['png', 'jpg'])
    if st.button("Reiniciar"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# --- 7. CHAT ---
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
        
        # MODO ZEOX
        if "zeox" in prompt.lower():
            st.write(">> 👑 ZEOX...")
            # Aquí iría Grok si tienes la clave, si no, salta error controlado
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
                 full_res = "⚠️ ZEOX inactivo (Falta clave)."

        # MODO ZEO (GEMINI PRO)
        else:
            if st.session_state.chat_session:
                try:
                    if archivo:
                        img = Image.open(archivo)
                        # Usamos el modelo que funcionó en el inicio
                        visor = genai.GenerativeModel(st.session_state.info_motor)
                        full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                    else:
                        full_res = st.session_state.chat_session.send_message(prompt).text
                except Exception as e:
                    full_res = f"⚠️ Error Motor: {e}"
            else:
                full_res = "⚠️ Sistema Apagado."
        
        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_log("ZEO", full_res)
