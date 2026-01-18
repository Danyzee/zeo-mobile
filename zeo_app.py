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

# --- 1. CONFIGURACIÓN VISUAL (NOIR HD - ESPAÑOL) ---
st.set_page_config(page_title="ZEO OS", layout="wide")

# CSS: ESTÉTICA DE LUJO MEJORADA (LETRAS MÁS CLARAS)
st.markdown("""
    <style>
    /* IMPORTAR FUENTES: 'Playfair' (Títulos lujo) y 'Inter' (Lectura perfecta) */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Inter:wght@300;400;600&display=swap');

    /* FONDO GENERAL */
    .stApp { 
        background-color: #080808; 
        color: #F5F5F5; /* Blanco humo para mejor lectura */
        font-family: 'Inter', sans-serif;
    }

    /* TÍTULOS (Headings) */
    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif !important;
        color: #FFFFFF !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* SIDEBAR (IZQUIERDA) */
    [data-testid="stSidebar"] { 
        background-color: #000000; 
        border-right: 1px solid #222;
    }
    
    /* CAJAS DE TEXTO (CHAT) */
    .stChatMessage { 
        font-family: 'Inter', sans-serif;
        font-size: 16px; /* Letra un poco más grande */
        line-height: 1.6;
    }
    
    /* INPUT DE TEXTO */
    .stChatInputContainer {
        border-color: #333 !important;
    }
    
    /* EL "CANVAS" (Marco derecho) */
    .css-1r6slb0 {
        background-color: #111;
        border: 1px dashed #444;
        border-radius: 10px;
        padding: 20px;
    }

    /* LÍNEAS DIVISORIAS SUTILES */
    hr { border-color: #333; }
    
    /* BOTONES */
    .stButton>button {
        background-color: #111;
        color: #FFF;
        border: 1px solid #444;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #D4AF37; /* Dorado al pasar el ratón */
        color: #D4AF37;
    }

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
        MEMORY_STATUS = "ACTIVA"
    else:
        MEMORY_STATUS = "OFF"
except:
    MEMORY_STATUS = "ERROR"

# --- 3. SKILL: CLIMA (ESPAÑOL) ---
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
                    "status": "ONLINE"
                }
            elif r.status_code == 401: return {"status": "ESPERANDO ACTIVACIÓN", "temp": "--", "desc": "Sin datos"}
            else: return {"status": "ERROR API", "temp": "--", "desc": "Fallo conexión"}
        except: return {"status": "ERROR RED", "temp": "--", "desc": "Fallo"}
    return {"status": "NO INSTALADA", "temp": "--", "desc": "Falta Clave"}

# TIEMPO REAL
try:
    zona_madrid = pytz.timezone('Europe/Madrid')
    AHORA = datetime.now(zona_madrid).strftime("%H:%M")
    FECHA_HOY = datetime.now(zona_madrid).strftime("%d de %B, %Y")
    # Traducción manual rápida de meses por si acaso el servidor está en inglés
    meses = {"January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril", "May": "Mayo", "June": "Junio", 
             "July": "Julio", "August": "Agosto", "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"}
    for eng, esp in meses.items():
        if eng in FECHA_HOY: FECHA_HOY = FECHA_HOY.replace(eng, esp)
except:
    AHORA = "00:00"
    FECHA_HOY = "FECHA DESC."

INFO_CLIMA = obtener_clima_madrid()

# --- 4. CEREBRO ---
PROMPT_ZEO = f"""
SISTEMA: ZEO OS.
CONTEXTO: {FECHA_HOY} | {AHORA} | Madrid. Clima: {INFO_CLIMA['temp']}C.
IDENTIDAD: Mayordomo Ejecutivo de Lijie Zhang (Sr. Eliot).
IDIOMA: SIEMPRE EN ESPAÑOL.
ESTILO:
- Elegante, profesional y culto.
- Formato limpio.
- Intelectualmente riguroso (refuta si es necesario).
NEGOCIOS: Ildan, RenLink.
"""
PROMPT_ZEOX = f"ERES ZEOX (GROK). Contexto: {AHORA}, Madrid. Idioma: ESPAÑOL. Tono: Sarcástico, Rebelde, Sin censura."

def iniciar_motor():
    modelos = ["gemini-2.5-pro", "gemini-pro-latest", "gemini-1.5-pro"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    return None, "FALLO MOTOR"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.info_motor = info
    st.session_state.messages = []

def guardar_log(role, text):
    if MEMORY_STATUS == "ACTIVA":
        try: hoja_memoria.append_row([str(datetime.now()), role, text])
        except: pass

# --- 5. INTERFAZ ---

# A. PANEL IZQUIERDO (MENÚ)
with st.sidebar:
    st.markdown("## ZEO OS")
    st.caption("SISTEMA OPERATIVO PERSONAL")
    
    st.markdown("---")
    
    st.markdown("#### 📡 CONEXIONES")
    st.markdown(f"**Motor:** GEMINI 2.5 PRO")
    st.markdown(f"**Memoria:** {MEMORY_STATUS}")
    # Color dinámico para el estado del clima
    st_clima = INFO_CLIMA['status']
    color_clima = "green" if "ONLINE" in st_clima else "orange" if "ESPERANDO" in st_clima else "red"
    st.markdown(f"**Sensores:** <span style='color:{color_clima}'>{st_clima}</span>", unsafe_allow_html=True)

    st.markdown("---")
    
    st.markdown("#### 🧠 SKILLS (Habilidades)")
    st.markdown("✓ **Racionamiento** [ACTIVO]")
    st.markdown("✓ **Clima Madrid** [ACTIVO]")
    st.markdown("🔒 **RenLink Analytics**")
    st.markdown("🔒 **Ildan Finance**")
    
    st.markdown("---")
    if st.button("REINICIAR SISTEMA"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

# B. ESTRUCTURA (CHAT + CANVAS)
col_chat, col_canvas = st.columns([2, 1.3])

# --- CENTRO: CHAT ---
with col_chat:
    st.markdown(f"### Buenas noches, Sr. Eliot.")
    st.caption(f"{FECHA_HOY} | MADRID, ESPAÑA")
    st.divider()
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escriba su orden..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        guardar_log("ELIOT", prompt)
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            full_res = "..."
            if "zeox" in prompt.lower():
                st.write(">> 👹 ZEOX:")
                if "CLAVE_GROK" in st.secrets and len(st.secrets["CLAVE_GROK"]) > 5:
                    try:
                        client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
                        res = client_grok.chat.completions.create(model="grok-3", messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}])
                        full_res = res.choices[0].message.content
                    except Exception as e: full_res = f"ERROR: {e}"
                else: full_res = "ACCESO DENEGADO (Falta Clave)"
            else:
                try:
                    full_res = st.session_state.chat_session.send_message(prompt).text
                except Exception as e: full_res = f"ERROR: {e}"
            
            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            guardar_log("ZEO", full_res)

# --- DERECHA: CANVAS (PANTALLA DE DATOS) ---
with col_canvas:
    # BLOQUE DE DATOS RÁPIDOS
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**HORA LOCAL**")
        st.markdown(f"<h1 style='font-size: 35px; margin:0;'>{AHORA}</h1>", unsafe_allow_html=True)
    with col_b:
        st.markdown("**TEMPERATURA**")
        temp_val = INFO_CLIMA['temp'] if INFO_CLIMA['temp'] != "--" else "--"
        st.markdown(f"<h1 style='font-size: 35px; margin:0;'>{temp_val}°</h1>", unsafe_allow_html=True)
        st.caption(f"{INFO_CLIMA['desc']}")

    st.markdown("<br>", unsafe_allow_html=True)

    # AQUÍ ESTÁ EL "CANVAS" VISUAL (El recuadro que pedía)
    st.markdown("##### 👁️ CANVAS DE PREVISUALIZACIÓN")
    
    # Creamos un contenedor oscuro que simula la pantalla de visualización
    with st.container(border=True):
        st.markdown("""
        <div style='height: 300px; display: flex; align-items: center; justify-content: center; color: #555;'>
            <i>(Esperando input visual o activación de Skill...)</i>
        </div>
        """, unsafe_allow_html=True)
        
        # Aquí es donde en el futuro ZEO pintará gráficas o webs
        if st.session_state.messages:
            ultimo = st.session_state.messages[-1]["content"]
            st.caption(f"⚙️ Procesando intención: {ultimo[:30]}...")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # SUBIDA DE ARCHIVOS (Fuera del canvas para no ensuciarlo)
    st.caption("ANALIZAR DOCUMENTO / IMAGEN")
    archivo = st.file_uploader("Subir evidencia", type=['png', 'jpg', 'pdf'], label_visibility="collapsed")
    if archivo:
        st.image(archivo, caption="Archivo cargado en memoria")
