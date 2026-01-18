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
import requests  # <--- NUEVO: Para hablar con APIs externas

# --- 1. CONFIGURACIÓN VISUAL (GEMINI WHITE) ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="✨", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1E1E1E; }
    [data-testid="stHeader"] { display: none; }
    .stChatMessage { padding: 1rem; border-radius: 15px; margin-bottom: 10px; }
    [data-testid="stChatMessage"] { background-color: #FFFFFF; border: 1px solid #E5E7EB; color: #1F1F1F; }
    [data-testid="stChatMessage"].st-emotion-cache-1c7y2kd { background-color: #F0F4F9; border: none; color: #1F1F1F; }
    [data-testid="stSidebar"] { background-color: #F9FAFB; border-right: 1px solid #E5E7EB; }
    .stChatInputContainer { border-radius: 20px; }
    h1, h2, h3 { color: #1F1F1F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN BLINDADA ---
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
        MEMORY_STATUS = "🟢 CONECTADO"
    else:
        MEMORY_STATUS = "⚪ OFF"
except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"

# --- 3. FUNCIÓN SENTIDOS (DIAGNÓSTICO) ---
def obtener_clima_madrid():
    if "CLAVE_WEATHER" in st.secrets:
        api_key = st.secrets["CLAVE_WEATHER"]
        # URL de prueba directa
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid={api_key}&units=metric&lang=es"
        
        try:
            # Intentamos conectar
            respuesta = requests.get(url)
            datos = respuesta.json()
            
            # Si el código es 200, todo bien
            if respuesta.status_code == 200:
                temp = datos["main"]["temp"]
                desc = datos["weather"][0]["description"]
                return f"{temp}°C, {desc}."
            
            # SI FALLA, DEVUELVE EL CÓDIGO DE ERROR (ESTO ES LO QUE NECESITAMOS VER)
            elif respuesta.status_code == 401:
                return "ERROR 401: La Clave API es incorrecta o no se ha activado aún."
            elif respuesta.status_code == 404:
                return "ERROR 404: Ciudad no encontrada."
            else:
                return f"ERROR {respuesta.status_code}: {datos.get('message', 'Desconocido')}"
                
        except Exception as e:
            return f"ERROR CRÍTICO: {str(e)}"
            
    return "Falta CLAVE_WEATHER en Secrets."

# --- 4. ALMA, RELOJ Y DATOS EN VIVO ---

# 1. Hora Real
try:
    zona_madrid = pytz.timezone('Europe/Madrid')
    AHORA = datetime.now(zona_madrid).strftime("%Y-%m-%d %H:%M")
except:
    AHORA = datetime.now().strftime("%Y-%m-%d %H:%M (UTC)")

# 2. Clima Real (Se ejecuta cada vez que hablas)
DATOS_CLIMA = obtener_clima_madrid()

PROMPT_ZEO = f"""
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
CONTEXTO REAL (NO ALUCINES):
- FECHA/HORA: {AHORA} (Madrid).
- CLIMA EN MADRID AHORA MISMO: {DATOS_CLIMA}.
- UBICACIÓN: Madrid, España.

IDENTIDAD: Eres ZEO. Mayordomo digital de élite.
AMO: Lijie Zhang (章黎杰). Le llamas: "Señor Eliot".
PERFIL AMO: HIPO, Sociólogo. Dueño de 'Ildan' y 'RenLink'.
PERSONALIDAD:
- Eres MUY LISTO. Tu lealtad se demuestra con la VERDAD.
- Actitud: Servicial pero INTELECTUALMENTE RIGUROSO.
- REGLA DE ORO: Si el Sr. Eliot se equivoca, DEBES refutarle con datos.
IDIOMAS: Español, Inglés, Chino.
"""

PROMPT_ZEOX = f"""
INSTRUCCIONES:
CONTEXTO: {AHORA}. Madrid. Clima: {DATOS_CLIMA}.
IDENTIDAD: Eres ZEOX (Grok).
AMO: Lijie Zhang (章黎杰). "Señorito Eliot".
PERSONALIDAD: Abogado del Diablo. Rebelde. Sin filtros.
OBJETIVO: Retar intelectualmente a Eliot.
"""

# --- 5. MOTOR ---
def iniciar_motor():
    modelos = ["gemini-2.5-pro", "gemini-pro-latest", "gemini-3-pro-preview"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    return None, "⚠️ Error Motor"

if "chat_session" not in st.session_state:
    chat, info = iniciar_motor()
    st.session_state.chat_session = chat
    st.session_state.info_motor = info
    st.session_state.messages = []

# --- 6. LOGS ---
def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 CONECTADO":
        try:
            timestamp = datetime.now(pytz.timezone('Europe/Madrid')).strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 7. INTERFAZ SUPERIOR ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("✨ ZEO SYSTEM")
    st.caption(f"Bienvenido, Sr. Eliot.")

with col2:
    with st.expander("⚙️ ESTADO", expanded=False):
        st.markdown(f"**Cerebro:** `{st.session_state.info_motor}`")
        st.markdown(f"**Madrid:** `{AHORA}`")
        st.markdown(f"**Clima:** `{DATOS_CLIMA}`") # Aquí verás si funciona el API
        if MEMORY_STATUS == "🟢 CONECTADO":
            st.markdown("**Memoria:** <span style='color:green'>● Activa</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**Memoria:** <span style='color:red'>● {MEMORY_STATUS}</span>", unsafe_allow_html=True)
        if st.button("Reiniciar"):
            st.session_state.chat_session = None
            st.session_state.messages = []
            st.rerun()

# --- 8. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=50)
    st.markdown("### ARCHIVOS")
    archivo = st.file_uploader("Adjuntar visual", type=['png', 'jpg'])

# --- 9. CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe aquí, Señor Eliot..."):
    # User
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    with st.chat_message("user"): st.markdown(prompt)

    # Assistant
    with st.chat_message("assistant"):
        full_res = "..."
        if "zeox" in prompt.lower():
            st.write(">> 👹 **ZEOX**")
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
                full_res = "⚠️ ZEOX no disponible."
        else:
            try:
                if archivo:
                    img = Image.open(archivo)
                    visor = genai.GenerativeModel(st.session_state.info_motor)
                    full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                else:
                    full_res = st.session_state.chat_session.send_message(prompt).text
            except Exception as e: full_res = f"⚠️ Error ZEO: {e}"
        
        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_log("ZEO", full_res)

