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

# --- 1. CONFIGURACIÓN VISUAL (ESTRUCTURA Y CONTRASTE) ---
st.set_page_config(page_title="ZEO OS", layout="wide")

# CSS: ARQUITECTURA VISUAL RIGUROSA
st.markdown("""
    <style>
    /* FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:wght@600&display=swap');

    /* 1. FONDO Y TEXTO GLOBAL (BLANCO PURO PARA LECTURA) */
    .stApp { 
        background-color: #050505; 
        color: #FFFFFF; 
        font-family: 'Inter', sans-serif;
    }
    
    /* 2. TEXTO DEL CHAT (CORRECCIÓN DE VISIBILIDAD) */
    .stChatMessage p, .stMarkdown p {
        color: #FFFFFF !important; /* Forza el blanco */
        font-weight: 400;
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* 3. LÍNEAS DIVISORIAS VERTICALES (COLUMNAS) */
    /* Apuntamos a las columnas de Streamlit para ponerles borde derecho */
    [data-testid="column"]:nth-of-type(1) {
        border-right: 1px solid #333333;
        padding-right: 20px;
    }
    [data-testid="column"]:nth-of-type(2) {
        border-right: 1px solid #333333;
        padding-right: 20px;
    }
    
    /* 4. SIDEBAR (MENÚ IZQUIERDO) */
    [data-testid="stSidebar"] { 
        background-color: #000000; 
        border-right: 1px solid #333333;
    }
    
    /* 5. ARREGLO DEL BOTÓN DE MENÚ (VISIBILIDAD) */
    /* No ocultamos el header completo, solo la decoración, para que el botón de abrir menú siga visible */
    [data-testid="stHeader"] {
        background-color: transparent;
    }
    [data-testid="stDecoration"] {
        display: none;
    }
    /* Forzamos que el icono de la hamburguesa sea blanco */
    button[kind="header"] {
        color: white !important;
    }

    /* 6. INPUT Y BOTONES */
    .stChatInputContainer {
        border-top: 1px solid #333;
        background-color: #050505;
    }
    /* Estilo del botón "+" (Popover) */
    button[kind="secondary"] {
        background-color: #111;
        color: white;
        border: 1px solid #444;
        border-radius: 50%; /* Redondo como en Gemini */
        width: 40px;
        height: 40px;
    }
    
    /* 7. CANVAS LIMPIO (SIN EMOJIS) */
    .css-1r6slb0 { border: 1px solid #333; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: white !important; }
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
        MEMORY_STATUS = "OFF"
except:
    MEMORY_STATUS = "ERROR"

# --- 3. CLIMA ---
def obtener_clima_madrid():
    if "CLAVE_WEATHER" in st.secrets:
        api_key = st.secrets["CLAVE_WEATHER"]
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid={api_key}&units=metric&lang=es"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                d = r.json()
                return {"temp": d["main"]["temp"], "desc": d["weather"][0]["description"].capitalize(), "status": "ONLINE"}
            elif r.status_code == 401: return {"status": "WAITING", "temp": "--", "desc": "Sin datos"}
        except: return {"status": "ERROR", "temp": "--", "desc": "Fallo red"}
    return {"status": "NO KEY", "temp": "--", "desc": "Falta Clave"}

try:
    zona_madrid = pytz.timezone('Europe/Madrid')
    AHORA = datetime.now(zona_madrid).strftime("%H:%M")
    FECHA_HOY = datetime.now(zona_madrid).strftime("%d.%m.%Y")
except:
    AHORA = "00:00"
    FECHA_HOY = "--.--.----"

INFO_CLIMA = obtener_clima_madrid()

# --- 4. MOTOR ---
PROMPT_ZEO = f"""
SISTEMA: ZEO OS.
CONTEXTO: {FECHA_HOY} | {AHORA} | Madrid. Clima: {INFO_CLIMA['temp']}C.
IDENTIDAD: Mayordomo Ejecutivo de Lijie Zhang (Sr. Eliot).
IDIOMA: SIEMPRE EN ESPAÑOL.
ESTILO: Elegante, directo, sin emojis en el texto.
NEGOCIOS: Ildan, RenLink.
"""
PROMPT_ZEOX = f"ERES ZEOX (GROK). Contexto: {AHORA}. Madrid. Idioma: ESPAÑOL. Sarcástico, sin censura."

def iniciar_motor():
    modelos = ["gemini-2.5-pro", "gemini-pro-latest", "gemini-1.5-pro"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    return None, "FAIL"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.info_motor = info
    st.session_state.messages = []

def guardar_log(role, text):
    if MEMORY_STATUS == "ACTIVE":
        try: hoja_memoria.append_row([str(datetime.now()), role, text])
        except: pass

# --- 5. LAYOUT DE 3 COLUMNAS (MENÚ | CHAT | CANVAS) ---

# Usamos 'ratio' para definir el ancho. Sidebar es automático.
# Aquí dividimos el espacio principal en Chat (2 partes) y Canvas (1.2 partes)
col_chat, col_canvas = st.columns([2, 1.2]) 

# --- A. SIDEBAR (MENÚ IZQUIERDO) ---
with st.sidebar:
    st.markdown("### ZEO OS")
    st.caption("SYSTEM v3.5")
    st.markdown("---")
    
    st.markdown("**CONNECTIONS**")
    st.markdown(f"ENGINE: GEMINI PRO")
    st.markdown(f"MEMORY: {MEMORY_STATUS}")
    # Color del estado
    color = "green" if "ONLINE" in INFO_CLIMA['status'] else "red"
    st.markdown(f"SENSORS: <span style='color:{color}'>{INFO_CLIMA['status']}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**SKILLS**")
    st.text("01 REASONING [ON]")
    st.text("02 METEO DATA [ON]")
    st.text("03 RENLINK DATA [OFF]")
    st.text("04 ILDAN FINANCE [OFF]")
    
    st.markdown("---")
    if st.button("REBOOT"):
        st.session_state.chat_session = None
        st.rerun()

# --- B. COLUMNA CENTRAL (CHAT) ---
with col_chat:
    st.markdown(f"## Sr. Eliot.")
    st.caption(f"MADRID | {FECHA_HOY}")
    
    # Espacio para mensajes
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # --- LA SOLUCIÓN DEL BOTÓN "+" ---
    # Colocamos un 'popover' justo encima o integrado visualmente
    # Usamos columnas para poner el "+" pequeñito
    
    col_plus, col_msg = st.columns([0.1, 0.9])
    
    # 1. El botón "+" (Popover)
    with st.popover("➕", help="Adjuntar archivos"):
        st.markdown("**Subir Evidencia**")
        archivo = st.file_uploader("Seleccionar archivo", type=['png', 'jpg', 'pdf'], label_visibility="collapsed")
        if archivo:
            st.success("Archivo cargado en memoria RAM.")
            st.image(archivo, width=200)

    # 2. Input de Chat
    if prompt := st.chat_input("Escriba su orden..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        guardar_log("ELIOT", prompt)
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            full_res = "..."
            if "zeox" in prompt.lower():
                st.write(">> ZEOX:")
                if "CLAVE_GROK" in st.secrets and len(st.secrets["CLAVE_GROK"]) > 5:
                    try:
                        client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
                        res = client_grok.chat.completions.create(model="grok-3", messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}])
                        full_res = res.choices[0].message.content
                    except Exception as e: full_res = f"ERR: {e}"
                else: full_res = "NO KEY"
            else:
                try:
                    # Si hay archivo cargado en el Popover, se lo pasamos
                    if archivo:
                        img = Image.open(archivo)
                        visor = genai.GenerativeModel(st.session_state.info_motor)
                        full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                    else:
                        full_res = st.session_state.chat_session.send_message(prompt).text
                except Exception as e: full_res = f"ERR: {e}"
            
            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            guardar_log("ZEO", full_res)

# --- C. COLUMNA DERECHA (CANVAS) ---
with col_canvas:
    st.markdown("### Visual Canvas")
    
    # Ticker de datos (Texto puro, sin emojis)
    c1, c2 = st.columns(2)
    c1.metric("LOCAL TIME", AHORA)
    c2.metric("TEMP (MAD)", f"{INFO_CLIMA['temp']}°", delta=None)
    
    st.divider()
    
    # El recuadro del Canvas (Limpio)
    st.markdown("**PREVIEW SCREEN**")
    
    with st.container(border=True):
        st.markdown("""
        <div style='height: 350px; display: flex; align-items: center; justify-content: center; color: #444; font-style: italic;'>
            WAITING FOR VISUAL OUTPUT
        </div>
        """, unsafe_allow_html=True)
        
    st.caption("SYSTEM STATUS: NOMINAL")
    
    # Log de intención
    if st.session_state.messages:
        last = st.session_state.messages[-1]["content"]
        st.text_area("PROCESSING INTENT:", value=last, height=70, disabled=True)
