import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json
import requests

# --- 1. CONFIGURACIÓN VISUAL (WHITE CANVAS / WIDE) ---
st.set_page_config(page_title="ZEO OS", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    /* ESTÉTICA BLANCA PREMIUM */
    .stApp { background-color: #FFFFFF; color: #1E1E1E; }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E5E7EB; }
    
    /* CHAT */
    [data-testid="stChatMessage"] { background-color: #FFFFFF; border: 1px solid #F0F0F0; border-radius: 12px; }
    [data-testid="stChatMessage"].st-emotion-cache-1c7y2kd { background-color: #F4F6F8; border: none; }

    /* BOTONES */
    .stButton>button { border-radius: 8px; border: 1px solid #E0E0E0; }
    
    /* HEADER LIMPIO */
    [data-testid="stHeader"] { background-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIONES ---
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
        MEMORY_STATUS = "🟢 ACTIVA"
    else: MEMORY_STATUS = "⚪ OFF"
except: MEMORY_STATUS = "🔴 ERROR"

# --- 3. CLIMA ---
def obtener_clima_madrid():
    if "CLAVE_WEATHER" in st.secrets:
        api_key = st.secrets["CLAVE_WEATHER"]
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid={api_key}&units=metric&lang=es"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                d = r.json()
                return {"temp": d["main"]["temp"], "desc": d["weather"][0]["description"], "status": "🟢 ONLINE"}
            elif r.status_code == 401: return {"status": "🟡 ESPERANDO", "temp": "--", "desc": "Clave"}
        except: return {"status": "🔴 ERROR RED", "temp": "--", "desc": "Fallo"}
    return {"status": "⚪ NO KEY", "temp": "--", "desc": "Falta"}

try:
    zona_madrid = pytz.timezone('Europe/Madrid')
    AHORA = datetime.now(zona_madrid).strftime("%H:%M")
    FECHA_HOY = datetime.now(zona_madrid).strftime("%Y-%m-%d")
except: AHORA = "--:--"

INFO_CLIMA = obtener_clima_madrid() 

# --- 4. CEREBRO (AUDITORÍA DE MODELOS PRO) ---
PROMPT_ZEO = f"""
SISTEMA: ZEO OS v3.2 (Pro Edition).
CONTEXTO: {FECHA_HOY} | {AHORA} | Madrid.
IDENTIDAD: Mayordomo de élite de Lijie Zhang (Sr. Eliot).
NEGOCIOS: Ildan, RenLink.
PERSONALIDAD: Inteligencia Máxima. Verdad Radical. No uses tono de asistente básico.
"""
PROMPT_ZEOX = f"ERES ZEOX (GROK). Sarcástico, oscuro, sin censura."

def iniciar_motor_auditado():
    # LISTA EXCLUSIVA DE MODELOS PRO (Sin Flash)
    # El sistema probará uno a uno y se quedará con el mejor disponible.
    jerarquia_pro = [
        "gemini-1.5-pro",          # El ESTÁNDAR DE ORO actual
        "gemini-1.5-pro-latest",   # Versión bleeding edge
        "gemini-pro"               # El clásico (1.0)
    ]
    
    log_intentos = []
    
    for m in jerarquia_pro:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping") # Prueba de conexión
            # Si pasa, este es el elegido
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m.upper()
        except Exception as e:
            log_intentos.append(f"{m}: Fallo")
            continue
            
    # Si llega aquí, NINGUNO funcionó
    return None, "NINGÚN PRO DISPONIBLE"

if "chat_session" not in st.session_state:
    chat, nombre_modelo = iniciar_motor_auditado()
    st.session_state.chat_session = chat
    st.session_state.info_motor = nombre_modelo
    st.session_state.messages = []

def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 ACTIVA":
        try: hoja_memoria.append_row([str(datetime.now()), role, text])
        except: pass

# --- 5. INTERFAZ ---

# A. SIDEBAR
with st.sidebar:
    st.markdown("## 🧬 ZEO OS")
    
    # DIAGNÓSTICO DEL MOTOR (AQUÍ VERÁ QUÉ VERSIÓN TIENE REALMENTE)
    if "NINGÚN" in st.session_state.info_motor:
        st.error(f"❌ {st.session_state.info_motor}")
        st.caption("Su clave API no permite acceso a modelos 1.5 Pro o Pro.")
    else:
        st.success(f"💎 MOTOR: {st.session_state.info_motor}")
    
    st.markdown("---")
    
    with st.expander("Estado del Sistema", expanded=True):
        st.markdown(f"**Memoria:** {MEMORY_STATUS}")
        estado_clima = INFO_CLIMA['status']
        color = "green" if "🟢" in estado_clima else "red"
        st.markdown(f"**Clima:** <span style='color:{color}'>{estado_clima}</span>", unsafe_allow_html=True)

    st.markdown("### 🧠 SKILLS")
    st.info("💬 **Reasoning Pro** (Activa)")
    st.success("🌦️ **Meteo Sense** (Activa)")
    st.markdown("🔒 **RenLink**")
    st.markdown("🔒 **Ildan**")
    
    st.markdown("---")
    if st.button("🔄 REBOOT"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# B. LAYOUT
col_chat, col_canvas = st.columns([2, 1])

# --- CHAT ---
with col_chat:
    st.markdown(f"#### 👋 Hola, Sr. Eliot.")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Dar orden..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        guardar_log("ELIOT", prompt)
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            full_res = "..."
            if "zeox" in prompt.lower():
                st.write(">> 👹 **ZEOX**")
                if "CLAVE_GROK" in st.secrets:
                    try:
                        client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
                        res = client_grok.chat.completions.create(model="grok-3", messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}])
                        full_res = res.choices[0].message.content
                    except Exception as e: full_res = f"Error Grok: {e}"
                else: full_res = "Falta clave Grok."
            else:
                if st.session_state.chat_session:
                    try:
                        full_res = st.session_state.chat_session.send_message(prompt).text
                    except Exception as e: full_res = f"Error: {e}"
                else:
                    full_res = "⚠️ ERROR: No se pudo conectar con ningún modelo PRO. Revise permisos de API."
            
            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            guardar_log("ZEO", full_res)

# --- CANVAS ---
with col_canvas:
    st.markdown("### 👁️ CANVAS")
    tab1, tab2 = st.tabs(["📊 DASHBOARD", "📂 ARCHIVOS"])
    
    with tab1:
        st.markdown("#### 📍 Madrid Status")
        col_a, col_b = st.columns(2)
        with col_a: st.metric("Hora", AHORA)
        with col_b: st.metric("Temp", f"{INFO_CLIMA['temp']}°C", delta=INFO_CLIMA['desc'])
        st.divider()
        st.markdown("#### 🤖 Active Intent")
        if st.session_state.messages:
            st.info(f"Procesando: '{st.session_state.messages[-1]['content'][:40]}...'")
        else: st.caption("Esperando...")

    with tab2:
        archivo = st.file_uploader("Analizar Doc/Img", key="canvas_uploader")
        if archivo: st.image(archivo, caption="Visualizando")
