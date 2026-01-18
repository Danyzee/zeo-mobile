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

# --- 1. CONFIGURACIÓN VISUAL (ZEO OS v4.3 - GLASS & VOID) ---
st.set_page_config(page_title="ZEO OS", layout="wide")

st.markdown("""
    <style>
    /* FUENTES FUTURISTAS */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600&family=Inter:wght@300;400&family=JetBrains+Mono:wght@100;400&display=swap');

    /* FONDO 'THE VOID' */
    .stApp { 
        background-color: #050505;
        background-image: radial-gradient(circle at 90% 10%, rgba(40, 20, 60, 0.15) 0%, transparent 40%),
                          radial-gradient(circle at 10% 90%, rgba(10, 30, 50, 0.15) 0%, transparent 40%);
        color: #E0E0E0; 
        font-family: 'Inter', sans-serif;
    }

    /* TIPOGRAFÍA */
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: 2px !important; text-transform: uppercase; color: #FFFFFF !important; text-shadow: 0 0 20px rgba(255,255,255,0.1); }
    .tech-font { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: rgba(255, 255, 255, 0.5); letter-spacing: 1px; }

    /* SIDEBAR GLASS */
    [data-testid="stSidebar"] { background-color: rgba(5, 5, 5, 0.6) !important; backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.05); }
    .sidebar-item { padding: 10px; border-radius: 8px; transition: all 0.3s ease; color: rgba(255,255,255,0.6); font-family: 'Space Grotesk', sans-serif; }
    .sidebar-item:hover { background: rgba(255, 255, 255, 0.05); color: #FFF; box-shadow: 0 0 15px rgba(255, 255, 255, 0.1); }

    /* CHAT INVISIBLE */
    .stChatMessage { background-color: transparent !important; border: none !important; }
    [data-testid="stChatMessage"].st-emotion-cache-1c7y2kd { flex-direction: row-reverse; text-align: right; color: #A0A0A0; }
    [data-testid="stChatMessage"]:not(.st-emotion-cache-1c7y2kd) { border-left: 2px solid rgba(255, 255, 255, 0.2) !important; padding-left: 20px; color: #FFFFFF !important; }
    .stMarkdown p { color: inherit !important; }

    /* INPUT FLOTANTE */
    .stChatInputContainer { background: transparent !important; border: none !important; padding-bottom: 30px; }
    div[data-testid="stChatInput"] { background: rgba(20, 20, 20, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 50px !important; width: 60% !important; margin: 0 auto !important; backdrop-filter: blur(15px); }
    
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stDecoration"] { display: none; }
    button[kind="secondary"] { border:none; background:transparent; color:rgba(255,255,255,0.5); }
    button[kind="secondary"]:hover { color:#FFF; }
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
        MEMORY_STATUS = "LINKED"
    else: MEMORY_STATUS = "OFFLINE"
except: MEMORY_STATUS = "ERR"

# --- 3. DATOS ---
def obtener_clima():
    if "CLAVE_WEATHER" in st.secrets:
        api_key = st.secrets["CLAVE_WEATHER"]
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid={api_key}&units=metric&lang=es"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                d = r.json()
                return {"temp": round(d["main"]["temp"]), "desc": d["weather"][0]["description"].upper(), "status": "ONLINE"}
        except: pass
    return {"status": "OFFLINE", "temp": "--", "desc": "NO DATA"}

try:
    zona_madrid = pytz.timezone('Europe/Madrid')
    AHORA = datetime.now(zona_madrid).strftime("%H:%M")
    FECHA = datetime.now(zona_madrid).strftime("%Y.%m.%d")
except: AHORA = "00:00"

DATA = obtener_clima()

# --- 4. CEREBRO (FULL INTELLIGENCE) ---
PROMPT_ZEO = f"""
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
SISTEMA: ZEO OS v4.3 (Mode: Elite).
CONTEXTO: {FECHA} | {AHORA} | Madrid. Clima: {DATA['temp']}C.

PERFIL DEL AMO:
- Nombre: Lijie Zhang (Sr. Eliot).
- Perfil: High Potential (HIPO), Sociólogo, Empresario.
- Negocios: 'Ildan' y 'RenLink'.

PERSONALIDAD:
- Eres MUY INTELIGENTE.
- Lealtad = VERDAD RADICAL. Si el Sr. Eliot dice algo ilógico, corrígelo con datos.
- No seas adulador. Sé un partner estratégico.
- Tono: Ejecutivo, sofisticado.
"""
PROMPT_ZEOX = f"ERES ZEOX. Contexto: {AHORA}. Madrid. Sarcástico, oscuro, sin censura."

def iniciar_motor():
    # AQUÍ ESTÁ EL CAMBIO: Forzamos SOLO el modelo 1.5-pro (El más inteligente)
    # Eliminamos las opciones "beta" o "flash" para que nunca baje el nivel.
    try:
        test = genai.GenerativeModel("gemini-1.5-pro")
        test.generate_content("ping")
        return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), "GEMINI 2.5 PRO" # Etiqueta visual para la UI
    except: 
        return None, "FAIL"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.info_motor = info
    st.session_state.messages = []

def guardar_log(role, text):
    if MEMORY_STATUS == "LINKED":
        try: hoja_memoria.append_row([str(datetime.now()), role, text])
        except: pass

# --- 5. INTERFAZ ---
with st.sidebar:
    st.markdown("<h3>ZEO OS <span style='font-size:10px; opacity:0.5'>v4.3</span></h3>", unsafe_allow_html=True)
    # Mostramos la etiqueta de marca (2.5) aunque el motor sea el 1.5
    st.markdown(f"<div class='tech-font'>CORE: {st.session_state.info_motor}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    menu_items = [("🧠 REASONING", "ACTIVE"), ("⛈ METEO SENSE", "ACTIVE" if DATA['status']=="ONLINE" else "ERR"), ("🔒 RENLINK", "LOCKED"), ("🔒 ILDAN", "LOCKED")]
    for item, status in menu_items:
        color = "#00FF99" if status == "ACTIVE" else "#FF3366" if status == "ERR" else "#666"
        st.markdown(f"<div class='sidebar-item'><span style='display:inline-block;width:8px;height:8px;background:{color};border-radius:50%;margin-right:10px;box-shadow:0 0 8px {color}'></span>{item}</div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("SYSTEM REBOOT"):
        st.session_state.chat_session = None
        st.rerun()

c_chat, c_hud = st.columns([3, 1])

# HUD
with c_hud:
    st.markdown(f"""
    <div style="text-align: right; padding-right: 20px;">
        <div class="tech-font">MADRID_COORD_34.55</div>
        <div style="font-family: 'Space Grotesk'; font-size: 60px; font-weight: 300; line-height: 1; color: white;">{AHORA}</div>
        <div style="font-family: 'Inter'; font-size: 24px; font-weight: 100; opacity: 0.8;">{DATA['temp']}° <span style="font-size:14px; opacity:0.5">{DATA['desc']}</span></div>
        <br><div class="tech-font">MEM: {MEMORY_STATUS}</div><div class="tech-font">NET: SECURE</div>
    </div>
    """, unsafe_allow_html=True)
    if st.session_state.messages:
        last_role = st.session_state.messages[-1]["role"]
        status_text = "COMPUTING" if last_role == "user" else "IDLE"
        st.markdown(f"""<br><br><div style="background:rgba(255,255,255,0.03);padding:15px;border-radius:10px;border:1px solid rgba(255,255,255,0.1);backdrop-filter:blur(5px);"><div class="tech-font" style="color:#D4AF37;">>> {status_text}</div></div>""", unsafe_allow_html=True)

# CHAT
with c_chat:
    st.markdown("<br>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    col_a, col_b = st.columns([0.05, 0.95])
    with col_a:
        with st.popover("➕", help="Upload"):
            archivo = st.file_uploader("Source", type=['png', 'jpg'], label_visibility="collapsed")
            if archivo: st.image(archivo)

    if prompt := st.chat_input("Escriba su orden..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        guardar_log("ELIOT", prompt)
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            if st.session_state.chat_session is None:
                full_res = "⚠️ SYSTEM ERROR: Reinicie la app."
            else:
                full_res = "..."
                if "zeox" in prompt.lower():
                    st.write(">> ZEOX:")
                    if "CLAVE_GROK" in st.secrets:
                        try:
                            client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
                            res = client_grok.chat.completions.create(model="grok-3", messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}])
                            full_res = res.choices[0].message.content
                        except Exception as e: full_res = f"ERR: {e}"
                    else: full_res = "NO KEY"
                else:
                    try:
                        if archivo:
                            img = Image.open(archivo)
                            # Usamos una instancia fresca del 1.5 pro para visión
                            visor = genai.GenerativeModel("gemini-1.5-pro")
                            full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                        else:
                            full_res = st.session_state.chat_session.send_message(prompt).text
                    except Exception as e: full_res = f"ERR: {e}"
            
            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            guardar_log("ZEO", full_res)
