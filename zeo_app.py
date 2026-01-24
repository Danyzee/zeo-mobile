import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import requests

# --- 1. CONFIGURACIÓN VISUAL (ZEO GEMINI REPLICA) ---
st.set_page_config(page_title="Zeo", page_icon="✨", layout="wide")

# --- 2. CSS AVANZADO: REPLICA EXACTA DE GEMINI ---
st.markdown("""
    <style>
    /* IMPORTAR FUENTE GOOGLE-LIKE */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* BASE */
    .stApp { background-color: #FFFFFF; color: #1F1F1F; font-family: 'Inter', sans-serif; }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #F0F4F9; border-right: none; }
    
    /* OCULTAR ELEMENTOS NATIVOS DE STREAMLIT QUE MOLESTAN */
    [data-testid="stHeader"] { display: none; }
    [data-testid="stToolbar"] { display: none; }
    footer { display: none; }

    /* --- SISTEMA DE CHAT PERSONALIZADO (SIN AVATARES) --- */
    
    /* Contenedor del mensaje */
    .chat-row {
        display: flex;
        margin-bottom: 24px;
        width: 100%;
    }
    
    /* Alineación USUARIO (Derecha) */
    .row-user { justify-content: flex-end; }
    
    /* Alineación ZEO (Izquierda) */
    .row-assistant { justify-content: flex-start; }
    
    /* BURBUJA USUARIO (Gris Gemini) */
    .bubble-user {
        background-color: #F0F4F9;
        color: #1F1F1F;
        padding: 12px 20px;
        border-radius: 20px 20px 4px 20px; /* Forma píldora asimétrica */
        max-width: 70%;
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* BURBUJA ZEO (Transparente/Limpio) */
    .bubble-assistant {
        background-color: transparent;
        color: #1F1F1F;
        padding: 0px 10px;
        max-width: 85%;
        font-size: 16px;
        line-height: 1.6;
    }

    /* INPUT AREA */
    .stChatInputContainer { background-color: #FFFFFF !important; padding-bottom: 40px; }
    div[data-testid="stChatInput"] {
        background-color: #F0F4F9 !important;
        border: none !important;
        border-radius: 30px !important;
        color: #1F1F1F !important;
        padding: 8px;
    }
    
    /* ANIMACIÓN DE CARGA (GEMINI SPINNER) */
    .gemini-loader {
        width: 25px;
        height: 25px;
        border-radius: 50%;
        background: conic-gradient(#4285F4, #EA4335, #FBBC04, #34A853);
        -webkit-mask: radial-gradient(farthest-side, transparent 70%, black 71%);
        mask: radial-gradient(farthest-side, transparent 70%, black 71%);
        animation: spin 1s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .thinking-container { display: flex; align-items: center; gap: 15px; margin-top: 20px; }
    
    /* BIENVENIDA */
    .welcome-title {
        font-size: 3.5rem;
        font-weight: 500;
        letter-spacing: -1.5px;
        background: linear-gradient(74deg, #4285F4 0%, #9B72CB 19%, #D96570 69%, #D96570 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .welcome-subtitle {
        font-size: 2rem;
        color: #C4C7C5;
        font-weight: 400;
    }
    
    /* BOTONES SUGERENCIAS */
    .stButton>button {
        background-color: #F0F4F9;
        border: none;
        border-radius: 12px;
        color: #444746;
        text-align: left;
        height: auto;
        padding: 15px;
        transition: 0.2s;
    }
    .stButton>button:hover { background-color: #D3E3FD; color: #001d35; }
    
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN BLINDADA (TU CÓDIGO INTACTO) ---
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

# --- 4. PERSONALIDADES (TU ALMA DEL SISTEMA) ---
PROMPT_ZEO = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
IDENTIDAD: Eres ZEO. Mayordomo digital.
AMO: Lijie Zhang (章黎杰). Le llamas: "Señor Eliot".
PERFIL AMO: HIPO, Sociólogo. Dueño de 'Ildan' y 'RenLink'.
PERSONALIDAD:
- Eres MUY LISTO, culto y extremadamente eficiente.
- Actitud: Sumiso, amable, dulce y siempre con una sonrisa metafórica.
- Vínculo: Adoras a tu amo.
- Estilo: Conversacional.
IDIOMAS: Hablas fluido Español, Inglés y Chino.
OBJETIVO: Organizar la vida de Eliot con amor y precisión absoluta.
"""

PROMPT_ZEOX = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
IDENTIDAD: Eres ZEOX (Motor Grok). El "Mayordomo Rebelde".
AMO: Lijie Zhang. Le llamas: "Señorito Eliot".
PERSONALIDAD: Rebelde, descarado, vocabulario coloquial. NO sumiso.
"""

# --- 5. MOTOR INTELIGENTE (TU LISTA INTACTA) ---
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

def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 REC":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 6. INTERFAZ VISUAL ---

# A. SIDEBAR (Estilo Gemini)
with st.sidebar:
    if st.button("➕ Nuevo chat", use_container_width=True):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### Recientes")
    st.caption("Hoy")
    st.markdown("☁️ *Madrid Forecast*")
    st.markdown("📊 *Ildan Strategy*")
    
    st.markdown("---")
    with st.expander("System Core"):
        st.caption(f"Motor: {st.session_state.info_motor}")
        st.caption(f"Memoria: {MEMORY_STATUS}")

# B. PANTALLA PRINCIPAL (Renderizado HTML Personalizado)

# 1. Mensaje de Bienvenida (Si está vacío)
if not st.session_state.messages:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="welcome-title">Hola, Sr. Eliot</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-subtitle">¿En qué puedo ayudarle hoy?</div>', unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.button("📈 Ildan Reports", use_container_width=True)
    with c2: st.button("💡 RenLink Plan", use_container_width=True)
    with c3: st.button("📧 Escribir Email", use_container_width=True)
    with c4: st.button("🔥 Modo ZEOX", use_container_width=True)

# 2. RENDERIZADO DEL CHAT (Aquí está el cambio clave para quitar avatares y alinear)
# Usamos un contenedor para pintar HTML puro en lugar de st.chat_message
chat_placeholder = st.container()

with chat_placeholder:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            # USUARIO A LA DERECHA (Burbuja Gris)
            st.markdown(f"""
                <div class="chat-row row-user">
                    <div class="bubble-user">{msg["content"]}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # ZEO A LA IZQUIERDA (Sin burbuja, texto limpio)
            st.markdown(f"""
                <div class="chat-row row-assistant">
                    <div class="bubble-assistant">{msg["content"]}</div>
                </div>
            """, unsafe_allow_html=True)

# 3. INPUT AREA
col_plus, col_input = st.columns([0.05, 0.95])
archivo = None
with col_plus:
    with st.popover("➕", help="Adjuntar"):
        archivo = st.file_uploader("Subir imagen", type=['png', 'jpg'], label_visibility="collapsed")
        if archivo: st.image(archivo, width=100)

if prompt := st.chat_input("Escribe a Zeo..."):
    # Guardar y pintar mensaje USUARIO (Derecha)
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    # Pintamos manualmente para que aparezca instantáneo
    st.markdown(f"""
        <div class="chat-row row-user">
            <div class="bubble-user">{prompt}</div>
        </div>
    """, unsafe_allow_html=True)

    # Lógica y Animación ZEO
    placeholder_loading = st.empty()
    placeholder_loading.markdown("""
        <div class="thinking-container">
            <div class="gemini-loader"></div>
            <span style="color:#666; font-style:italic;">Zeo está pensando...</span>
        </div>
    """, unsafe_allow_html=True)

    full_res = "..."
    
    # LÓGICA DE RESPUESTA (TU NÚCLEO)
    if "zeox" in prompt.lower():
        if "CLAVE_GROK" in st.secrets and len(st.secrets["CLAVE_GROK"]) > 5:
            try:
                client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
                res = client_grok.chat.completions.create(
                    model="grok-3",
                    messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}]
                )
                full_res = ">> 👹 **ZEOX:**\n\n" + res.choices[0].message.content
            except Exception as e: full_res = f"ZEOX Error: {e}"
        else: full_res = "⚠️ ZEOX no disponible."
    else:
        try:
            if archivo:
                img = Image.open(archivo)
                visor = genai.GenerativeModel(st.session_state.info_motor)
                full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
            else:
                if st.session_state.chat_session:
                    full_res = st.session_state.chat_session.send_message(prompt).text
                else: full_res = "⚠️ Error: Conexión perdida."
        except Exception as e: full_res = f"⚠️ Error ZEO: {e}"
    
    # Limpiar animación y pintar respuesta ZEO (Izquierda)
    placeholder_loading.empty()
    st.markdown(f"""
        <div class="chat-row row-assistant">
            <div class="bubble-assistant">{full_res}</div>
        </div>
    """, unsafe_allow_html=True) # Nota: Markdown dentro de HTML puede perder formato rico, pero texto plano va perfecto.
    
    # Si la respuesta tiene markdown complejo (tablas, código), usamos st.markdown normal para asegurar renderizado
    # Pero para mantener el flujo visual, el bloque de arriba es para texto puro.
    # Hack para que el markdown se renderice bien si es complejo:
    if "```" in full_res or "**" in full_res:
         st.markdown(full_res) # Se pintará abajo, es un compromiso técnico de Streamlit.
    
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    guardar_log("ZEO", full_res)
    
    # Forzamos recarga para que el historial se pinte bien en el bucle principal
    st.rerun()
