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

# --- 1. CONFIGURACIÓN VISUAL (NOIR & ELEGANT) ---
st.set_page_config(page_title="ZEO OS", layout="wide")

# CSS: ESTÉTICA DE LUJO (BLACK & GOLD/PLATINUM)
st.markdown("""
    <style>
    /* IMPORTAR FUENTES ELEGANTES */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Lato:wght@300;400&display=swap');

    /* FONDO GENERAL */
    .stApp { 
        background-color: #050505; 
        color: #E0E0E0;
        font-family: 'Lato', sans-serif;
    }

    /* TIPOGRAFÍA */
    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif !important;
        color: #F0F0F0 !important;
        font-weight: 400;
        letter-spacing: 1px;
    }
    
    /* SIDEBAR (IZQUIERDA) - FONDO NEGRO Y BORDE DERECHO */
    [data-testid="stSidebar"] { 
        background-color: #000000; 
        border-right: 1px solid #333333;
    }
    
    /* COLUMNAS Y DIVISORES */
    /* Forzamos línea divisoria entre el Chat y el Canvas */
    div[data-testid="column"]:nth-of-type(2) {
        border-right: 1px solid #333333;
        padding-right: 20px;
    }
    div[data-testid="column"]:nth-of-type(3) {
        padding-left: 20px;
    }

    /* CAJAS DE CHAT (MINIMALISTAS) */
    .stChatMessage { 
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #1A1A1A !important;
        border-radius: 0px !important;
        padding: 1.5rem 0;
    }
    
    /* INPUT DE TEXTO */
    .stChatInputContainer {
        background-color: #050505;
        border-top: 1px solid #333;
    }
    div[data-testid="stChatInput"] {
        border-radius: 0px;
        border: 1px solid #333;
        background-color: #0A0A0A;
        color: white;
    }

    /* BOTONES ESTILIZADOS */
    .stButton>button {
        background-color: #0A0A0A;
        color: #A0A0A0;
        border: 1px solid #333;
        border-radius: 0px;
        font-family: 'Lato', sans-serif;
        text-transform: uppercase;
        font-size: 0.8rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        border-color: #FFFFFF;
        color: #FFFFFF;
    }
    
    /* OCULTAR ELEMENTOS INNECESARIOS */
    [data-testid="stHeader"] { display: none; }
    
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
        MEMORY_STATUS = "ACTIVE"
    else:
        MEMORY_STATUS = "DISCONNECTED"
except:
    MEMORY_STATUS = "SYSTEM ERROR"

# --- 3. SKILL: CLIMA (TEXTO PURO, SIN EMOJIS) ---
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
                    "desc": d["weather"][0]["description"].capitalize(),
                    "hum": d["main"]["humidity"],
                    "status": "ONLINE"
                }
            elif r.status_code == 401: return {"status": "WAITING AUTH", "temp": "--", "desc": "No Data"}
            else: return {"status": "API ERROR", "temp": "--", "desc": "Connection Failed"}
        except: return {"status": "NETWORK ERROR", "temp": "--", "desc": "Failed"}
    return {"status": "NOT INSTALLED", "temp": "--", "desc": "Missing Key"}

# DATOS EN TIEMPO REAL
try:
    zona_madrid = pytz.timezone('Europe/Madrid')
    AHORA = datetime.now(zona_madrid).strftime("%H:%M")
    FECHA_HOY = datetime.now(zona_madrid).strftime("%d %B %Y").upper()
except:
    AHORA = "00:00"
    FECHA_HOY = "UNKNOWN DATE"

INFO_CLIMA = obtener_clima_madrid()

# --- 4. CEREBRO ---
PROMPT_ZEO = f"""
SISTEMA: ZEO OS.
CONTEXTO: {FECHA_HOY} | {AHORA} | Madrid. Clima: {INFO_CLIMA['temp']}C.
IDENTIDAD: Mayordomo Ejecutivo de Lijie Zhang (Sr. Eliot).
ESTILO DE RESPUESTA:
- NO uses emojis.
- Usa un tono extremadamente elegante, profesional y culto.
- Formato limpio y estructurado.
- Eres intelectualmente riguroso.
NEGOCIOS: Ildan, RenLink.
"""
PROMPT_ZEOX = f"ERES ZEOX (GROK). Contexto: {AHORA}, Madrid. Tono: Sarcástico, Rebelde, Sin censura. NO uses emojis, solo palabras crudas."

def iniciar_motor():
    modelos = ["gemini-2.5-pro", "gemini-pro-latest", "gemini-1.5-pro"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    return None, "ENGINE FAILURE"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.info_motor = info
    st.session_state.messages = []

def guardar_log(role, text):
    if MEMORY_STATUS == "ACTIVE":
        try: hoja_memoria.append_row([str(datetime.now()), role, text])
        except: pass

# --- 5. INTERFAZ: DISEÑO DE TRES PANELES ---

# A. PANEL IZQUIERDO (SIDEBAR - MENU)
with st.sidebar:
    st.markdown("## ZEO OS")
    st.markdown(f"<p style='font-size: 10px; color: #666; letter-spacing: 2px;'>SYSTEM STATUS: {INFO_CLIMA['status']}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("#### CONNECTIONS")
    st.caption("CORE SYSTEM")
    st.markdown(f"**Engine:** GEMINI 2.5 PRO")
    st.markdown(f"**Memory:** {MEMORY_STATUS}")
    st.markdown(f"**Sensors:** {INFO_CLIMA['status']}")

    st.markdown("---")
    
    st.markdown("#### SKILLS LIBRARY")
    st.caption("AVAILABLE MODULES")
    st.markdown("**01.** REASONING ENGINE [ACTIVE]")
    st.markdown("**02.** METEO DATA [ACTIVE]")
    st.markdown("**03.** RENLINK ANALYTICS [LOCKED]")
    st.markdown("**04.** ILDAN FINANCE [LOCKED]")
    
    st.markdown("---")
    if st.button("REBOOT SYSTEM"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# B. ESTRUCTURA PRINCIPAL (CHAT + CANVAS)
col_chat, col_canvas = st.columns([2, 1.2])

# --- PANEL CENTRAL: CHAT ---
with col_chat:
    st.markdown(f"### Good evening, Mr. Eliot.")
    st.markdown(f"<p style='color: #666; font-size: 12px;'>{FECHA_HOY} | MADRID</p>", unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Enter command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        guardar_log("ELIOT", prompt)
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            full_res = "..."
            if "zeox" in prompt.lower():
                st.write(">> ZEOX SYSTEM:")
                if "CLAVE_GROK" in st.secrets and len(st.secrets["CLAVE_GROK"]) > 5:
                    try:
                        client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
                        res = client_grok.chat.completions.create(model="grok-3", messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}])
                        full_res = res.choices[0].message.content
                    except Exception as e: full_res = f"ERROR: {e}"
                else: full_res = "ACCESS DENIED (NO KEY)"
            else:
                try:
                    full_res = st.session_state.chat_session.send_message(prompt).text
                except Exception as e: full_res = f"ERROR: {e}"
            
            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            guardar_log("ZEO", full_res)

# --- PANEL DERECHO: CANVAS (VISUALIZADOR) ---
with col_canvas:
    st.markdown("### Visual Canvas")
    
    # DATOS ESTILO "TICKER" FINANCIERO
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**LOCAL TIME**")
        st.markdown(f"<h1 style='font-size: 40px; margin:0;'>{AHORA}</h1>", unsafe_allow_html=True)
    with col_b:
        st.markdown("**TEMPERATURE**")
        temp_val = INFO_CLIMA['temp'] if INFO_CLIMA['temp'] != "--" else "N/A"
        st.markdown(f"<h1 style='font-size: 40px; margin:0;'>{temp_val}°</h1>", unsafe_allow_html=True)
        st.caption(f"{INFO_CLIMA['desc']}")
    
    st.markdown("---")
    
    # VISUALIZADOR DE INTENCIÓN / ARCHIVOS
    tab1, tab2 = st.tabs(["ACTIVE PROCESS", "DATA INPUT"])
    
    with tab1:
        st.markdown("**CURRENT TASK**")
        if st.session_state.messages:
            ultimo = st.session_state.messages[-1]["content"]
            st.markdown(f"> *Processing: {ultimo[:40]}...*")
        else:
            st.markdown("> *System Idle. Awaiting input.*")
            
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("**SYSTEM LOGS:**")
        st.code(f"USER: Authorized\nLOC: Madrid\nAPI: {INFO_CLIMA['status']}", language="yaml")

    with tab2:
        archivo = st.file_uploader("UPLOAD SOURCE", type=['png', 'jpg', 'pdf'])
        if archivo:
            st.image(archivo)
