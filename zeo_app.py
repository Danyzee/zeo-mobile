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

# --- 1. CONFIGURACIÓN VISUAL (MODO CANVAS / WIDE) ---
st.set_page_config(page_title="ZEO OS", page_icon="✨", layout="wide")

# CSS PREMIUM: DISEÑO DE 3 COLUMNAS (FONDO BLANCO)
st.markdown("""
    <style>
    /* FONDO Y TEXTO */
    .stApp { background-color: #FFFFFF; color: #1E1E1E; }
    
    /* SIDEBAR (MENÚ IZQUIERDA) */
    [data-testid="stSidebar"] { 
        background-color: #F8F9FA; 
        border-right: 1px solid #E5E7EB;
    }
    
    /* CHAT (COLUMNA CENTRAL) */
    .stChatMessage { 
        border-radius: 12px; 
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stChatMessage"] { background-color: #FFFFFF; border: 1px solid #F0F0F0; }
    [data-testid="stChatMessage"].st-emotion-cache-1c7y2kd { background-color: #F4F6F8; border: none; }

    /* CANVAS (COLUMNA DERECHA) - ESTILO TARJETA */
    div[data-testid="column"] {
        padding: 10px;
    }
    
    /* TÍTULOS */
    h1, h2, h3 { font-family: 'Helvetica', sans-serif; font-weight: 600; color: #202124; }
    
    /* BOTONES */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
    }
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
    else:
        MEMORY_STATUS = "⚪ OFF"
except:
    MEMORY_STATUS = "🔴 ERROR"

# --- 3. SKILL: CLIMA ---
def obtener_clima_madrid():
    if "CLAVE_WEATHER" in st.secrets:
        api_key = st.secrets["CLAVE_WEATHER"]
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid={api_key}&units=metric&lang=es"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                d = r.json()
                return {
                    "temp": d["main"]["temp"],
                    "desc": d["weather"][0]["description"],
                    "hum": d["main"]["humidity"],
                    "status": "🟢 ONLINE"
                }
            elif r.status_code == 401: return {"status": "🟡 ESPERANDO ACTIVACIÓN", "temp": "--", "desc": "Sin datos"}
            else: return {"status": "🔴 ERROR API", "temp": "--", "desc": "Fallo conexión"}
        except: return {"status": "🔴 ERROR RED", "temp": "--", "desc": "Fallo red"}
    return {"status": "⚪ NO INSTALADA", "temp": "--", "desc": "Falta Clave"}

# DATOS EN TIEMPO REAL
try:
    zona_madrid = pytz.timezone('Europe/Madrid')
    AHORA = datetime.now(zona_madrid).strftime("%H:%M")
    FECHA_HOY = datetime.now(zona_madrid).strftime("%Y-%m-%d")
except:
    AHORA = "Error Reloj"
    FECHA_HOY = "----"

INFO_CLIMA = obtener_clima_madrid() 

# --- 4. CEREBRO (PROMPTS MEJORADOS PARA QUE NO SEA TONTO) ---
PROMPT_ZEO = f"""
SISTEMA: ZEO OS v3.0 (Mode: Canvas).
CONTEXTO: {FECHA_HOY} | {AHORA} | Madrid. Clima: {INFO_CLIMA['temp']}C.
IDENTIDAD: Mayordomo digital de élite de Lijie Zhang (Sr. Eliot).
NEGOCIOS: Ildan (Finanzas), RenLink (RRHH).
PERSONALIDAD: 
- Eres EXTREMADAMENTE INTELIGENTE (HIPO).
- No seas adulador. Si Eliot se equivoca, corrígele con datos (Verdad Radical).
- Tono: Ejecutivo y claro.
"""
PROMPT_ZEOX = f"ERES ZEOX (GROK). Contexto: {AHORA}, Madrid. Sé rebelde, sarcástico y reta al Sr. Eliot."

def iniciar_motor():
    # CORRECCIÓN DE SEGURIDAD: Ponemos el 1.5-pro primero para evitar el error de conexión
    modelos = ["gemini-1.5-pro", "gemini-pro"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), "GEMINI 2.5 (Simulado)"
        except: continue
    return None, "⚠️ Error Motor"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.info_motor = info
    st.session_state.messages = []

def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 ACTIVA":
        try: hoja_memoria.append_row([str(datetime.now()), role, text])
        except: pass

# --- 5. INTERFAZ ---

# A. SIDEBAR
with st.sidebar:
    st.markdown("## 🧬 ZEO OS")
    st.caption(f"v3.0 | {st.session_state.info_motor}")
    
    st.markdown("---")
    
    st.markdown("### 🔌 CONEXIONES")
    with st.expander("Hardware / APIs", expanded=True):
        st.markdown(f"**Cerebro:** 🟢 Gemini 1.5 Pro")
        st.markdown(f"**Memoria:** {MEMORY_STATUS}")
        
        estado_clima = INFO_CLIMA['status']
        if "🟢" in estado_clima: color = "green"
        elif "🟡" in estado_clima: color = "orange"
        else: color = "red"
        st.markdown(f"**Sentidos:** <span style='color:{color}'>{estado_clima}</span>", unsafe_allow_html=True)

    st.markdown("### 🧠 SKILLS")
    st.info("💬 **Chat & Reasoning** (Activa)")
    st.success("🌦️ **Meteo Sense** (Activa)")
    st.markdown("🔒 **RenLink Analytics** (Inactiva)")
    st.markdown("🔒 **Ildan Finance** (Inactiva)")
    
    st.markdown("---")
    if st.button("🔄 REBOOT SYSTEM"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# B. LAYOUT
col_chat, col_canvas = st.columns([2, 1])

# --- COLUMNA CENTRAL ---
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
                    except Exception as e: full_res = f"Error: {e}"
                else: full_res = "Falta clave Grok."
            else:
                try:
                    if st.session_state.chat_session:
                        full_res = st.session_state.chat_session.send_message(prompt).text
                    else:
                        full_res = "Error: Motor desconectado."
                except Exception as e: full_res = f"Error: {e}"
            
            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            guardar_log("ZEO", full_res)

# --- COLUMNA DERECHA ---
with col_canvas:
    st.markdown("### 👁️ CANVAS PREVIEW")
    
    tab1, tab2 = st.tabs(["📊 DASHBOARD", "📂 ARCHIVOS"])
    
    with tab1:
        st.markdown("#### 📍 Madrid Status")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Hora", AHORA)
        with col_b:
            st.metric("Temp", f"{INFO_CLIMA['temp']}°C", delta=INFO_CLIMA['desc'])
        
        st.divider()
        
        st.markdown("#### 🤖 Active Intent")
        if st.session_state.messages:
            ultimo_msg = st.session_state.messages[-1]["content"]
            st.info(f"Procesando: '{ultimo_msg[:50]}...'")
        else:
            st.caption("Esperando órdenes...")

    with tab2:
        archivo = st.file_uploader("Analizar Doc/Img", key="canvas_uploader")
        if archivo:
            st.image(archivo, caption="Visualizando en Canvas")
