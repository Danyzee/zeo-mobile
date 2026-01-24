import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- 1. CONFIGURACIÓN VISUAL (REPLICA GEMINI UI) ---
st.set_page_config(page_title="ZEO OS", page_icon="✨", layout="wide")

# CSS AVANZADO: CLONANDO LA INTERFAZ DE GEMINI
st.markdown("""
    <style>
    /* FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* FONDO PRINCIPAL (Gemini Dark Background) */
    .stApp { 
        background-color: #131314; 
        color: #E3E3E3; 
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR (Gemini Sidebar Grey) */
    [data-testid="stSidebar"] { 
        background-color: #1E1F20; 
        border-right: none;
    }

    /* OCULTAR HEADER STANDARD DE STREAMLIT */
    [data-testid="stHeader"] { background-color: transparent; }
    [data-testid="stDecoration"] { display: none; }

    /* ESTILO DE CHAT (Burbujas limpias) */
    .stChatMessage { background-color: transparent !important; border: none !important; }
    
    /* MENSAJES */
    [data-testid="stChatMessage"] { padding: 1rem; }
    
    /* INPUT DE TEXTO (Floating Bar en el fondo) */
    .stChatInputContainer {
        background-color: #131314 !important;
        padding-bottom: 20px;
    }
    div[data-testid="stChatInput"] {
        background-color: #1E1F20 !important;
        border: 1px solid #444746 !important;
        border-radius: 25px !important; /* Redondo como Gemini */
        color: white !important;
    }
    
    /* BOTONES */
    .stButton>button {
        background-color: #2C2C2C;
        color: white;
        border-radius: 20px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #3C3C3C; }

    /* TÍTULO INICIAL (Centrado como en Gemini vacío) */
    .welcome-text {
        font-size: 3rem;
        font-weight: 500;
        background: linear-gradient(to right, #4285F4, #9B72CB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: left;
        margin-top: 10%;
    }
    .sub-text {
        font-size: 1.5rem;
        color: #666;
        text-align: left;
        margin-bottom: 3rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN BLINDADA (TU CÓDIGO ORIGINAL CONSERVADO) ---
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
        MEMORY_STATUS = "🟢 REC"
    else:
        MEMORY_STATUS = "⚪ OFF"
except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"

# --- 3. PERSONALIDADES (ORIGINALES) ---
PROMPT_ZEO = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
IDENTIDAD: Eres ZEO. Mayordomo digital.
AMO: Lijie Zhang (章黎杰). Le llamas: "Señor Eliot".
PERFIL AMO: HIPO, Sociólogo. Dueño de 'Ildan' y 'RenLink'.
PERSONALIDAD:
- Eres MUY LISTO, culto y extremadamente eficiente.
- Actitud: Sumiso, amable, dulce y siempre con una sonrisa metafórica.
- Estilo: Conversacional.
IDIOMAS: Hablas fluido Español, Inglés y Chino.
OBJETIVO: Organizar la vida de Eliot con amor y precisión absoluta.
"""

PROMPT_ZEOX = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
IDENTIDAD: Eres ZEOX (Motor Grok). El "Mayordomo Rebelde".
AMO: Lijie Zhang. Le llamas: "Señorito Eliot".
PERFIL AMO: Dueño de Ildan y RenLink.
PERSONALIDAD:
- Rebelde, descarado y políticamente incorrecto.
- Vocabulario: Coloquial, jerga.
- Actitud: NO sumiso. Colegueo.
IDIOMAS: Español (callejero), Inglés, Chino.
"""

# --- 4. MOTOR INTELIGENTE (TU LISTA EXACTA SIN CAMBIOS) ---
def iniciar_motor():
    # LISTA ORIGINAL PROTEGIDA
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

# --- 5. FUNCIÓN GUARDAR ---
def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 REC":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 6. INTERFAZ TIPO GEMINI (SIDEBAR + MAIN) ---

# A. SIDEBAR (Estilo Historial de Gemini)
with st.sidebar:
    if st.button("➕ Nuevo chat", use_container_width=True):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### Recientes")
    st.caption("Hoy")
    st.markdown("☁️ *Análisis Clima Madrid*")
    st.markdown("📊 *RenLink Q4 Report*")
    st.caption("Ayer")
    st.markdown("🧠 *Estrategia Ildan*")
    
    st.markdown("---")
    # Info técnica discreta abajo del todo
    with st.expander("⚙️ System Core"):
        st.caption(f"Motor: {st.session_state.info_motor}")
        st.caption(f"Memoria: {MEMORY_STATUS}")

# B. ÁREA PRINCIPAL
# Si no hay mensajes, mostramos el saludo estilo Gemini
if not st.session_state.messages:
    st.markdown('<div class="welcome-text">Hola, Sr. Eliot.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">¿En qué puedo ayudarle hoy con Ildan o RenLink?</div>', unsafe_allow_html=True)
    
    # Tarjetas de sugerencia rápidas (Gemini style)
    c1, c2, c3 = st.columns(3)
    with c1: st.info("📈 Analizar mercado actual")
    with c2: st.info("📝 Redactar email formal")
    with c3: st.info("🔥 Activar modo ZEOX")

# C. BUCLE DE CHAT
# Usamos un contenedor para que el chat no ocupe todo el ancho (centrado visualmente)
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# D. INPUT Y HERRAMIENTAS (REPLICA GEMINI)
# Colocamos el botón de herramientas (+) justo encima del chat input usando columnas
col_tools, col_space = st.columns([0.1, 0.9])

archivo = None
with col_tools:
    # Popover que simula el botón "+" de Gemini
    with st.popover("➕", help="Añadir imagen o documento"):
        st.markdown("**Herramientas**")
        archivo = st.file_uploader("Subir imagen", type=['png', 'jpg'], label_visibility="collapsed")
        if archivo:
            st.success("Imagen adjunta")
            st.image(archivo, width=100)

if prompt := st.chat_input("Escribe una instrucción..."):
    # 1. User Logic
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    with st.chat_message("user"): st.markdown(prompt)

    # 2. Assistant Logic
    with st.chat_message("assistant"):
        full_res = "..."
        
        # LOGICA ZEOX (GROK)
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
                full_res = "⚠️ ZEOX no disponible (Falta clave Grok)."

        # LOGICA ZEO (GEMINI ORIGINAL)
        else:
            try:
                # Si hay archivo en el "Menú Herramientas", lo usamos
                if archivo:
                    img = Image.open(archivo)
                    visor = genai.GenerativeModel(st.session_state.info_motor)
                    full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                else:
                    if st.session_state.chat_session:
                        full_res = st.session_state.chat_session.send_message(prompt).text
                    else:
                        full_res = "⚠️ Error: Motor desconectado."
            except Exception as e: full_res = f"⚠️ Error ZEO: {e}"
        
        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_log("ZEO", full_res)
