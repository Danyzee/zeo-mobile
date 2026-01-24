import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- 1. CONFIGURACIÓN VISUAL (ZEO / GEMINI REPLICA) ---
st.set_page_config(page_title="Zeo", page_icon="✨", layout="wide")

# CSS: CLONACIÓN VISUAL + ANIMACIÓN DE CARGA
st.markdown("""
    <style>
    /* FUENTE */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* BASE */
    .stApp { background-color: #FFFFFF; color: #1F1F1F; font-family: 'Inter', sans-serif; }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #F0F4F9; border-right: none; }
    
    /* CHAT */
    .stChatMessage { background-color: transparent !important; border: none !important; }
    
    /* INPUT */
    .stChatInputContainer { background-color: #FFFFFF !important; padding-bottom: 30px; }
    div[data-testid="stChatInput"] {
        background-color: #F0F4F9 !important;
        border: none !important;
        border-radius: 24px !important;
        color: #1F1F1F !important;
    }
    
    /* OCULTAR HEADER */
    [data-testid="stHeader"] { display: none; }
    
    /* ANIMACIÓN DE CARGA TIPO GEMINI (EL CÍRCULO) */
    .gemini-loader {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: conic-gradient(#4285F4, #EA4335, #FBBC04, #34A853); /* Colores Google */
        -webkit-mask: radial-gradient(farthest-side, transparent 70%, black 71%);
        mask: radial-gradient(farthest-side, transparent 70%, black 71%);
        animation: spin 1s linear infinite;
        margin-left: 10px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .thinking-text {
        font-size: 14px;
        color: #666;
        margin-left: 15px;
        font-style: italic;
        display: flex;
        align-items: center;
    }

    /* TEXTO BIENVENIDA */
    .welcome-text {
        font-size: 3.5rem;
        font-weight: 500;
        letter-spacing: -1px;
        background: linear-gradient(74deg, #4285F4 0%, #9B72CB 19%, #D96570 69%, #D96570 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN BLINDADA (NÚCLEO INTACTO) ---
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

# --- 3. PERSONALIDADES (INTACTAS) ---
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

# --- 4. MOTOR INTELIGENTE (TU LISTA OFICIAL) ---
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

# --- 5. INTERFAZ: SIDEBAR "ZEO" ---
with st.sidebar:
    # Nuevo Chat
    if st.button("➕ Nuevo chat", use_container_width=True):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### Recientes")
    st.caption("Hoy")
    st.markdown("☁️ *Madrid Climate*")
    st.markdown("📊 *RenLink Data*")
    
    st.markdown("---")
    with st.expander("Ajustes"):
        st.caption(f"Motor: {st.session_state.info_motor}")
        st.caption(f"Memoria: {MEMORY_STATUS}")

# --- 6. PANTALLA PRINCIPAL ---

# Mensaje de bienvenida si está vacío
if not st.session_state.messages:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="welcome-text">Hola, Sr. Eliot</div>', unsafe_allow_html=True)
    st.markdown('<h2 style="color: #C4C7C5; font-weight: 400;">¿Cómo puedo ayudarle hoy?</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tarjetas
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.button("📈 Ildan Reports", use_container_width=True)
    with c2: st.button("💡 RenLink Strategy", use_container_width=True)
    with c3: st.button("📧 Escribir Email", use_container_width=True)
    with c4: st.button("🔥 Modo ZEOX", use_container_width=True)

# Contenedor del Chat
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 7. INPUT Y RESPUESTA CON ANIMACIÓN ---
col_plus, col_input = st.columns([0.05, 0.95])
archivo = None
with col_plus:
    with st.popover("➕", help="Adjuntar"):
        archivo = st.file_uploader("Subir imagen", type=['png', 'jpg'], label_visibility="collapsed")
        if archivo: st.image(archivo, width=100)

if prompt := st.chat_input("Escribe a Zeo..."):
    # 1. Mostrar User
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    with st.chat_message("user"): st.markdown(prompt)

    # 2. GENERACIÓN DE RESPUESTA CON ANIMACIÓN "GEMINI LOADER"
    with st.chat_message("assistant"):
        # AQUI ESTÁ LA MAGIA: Un placeholder vacío
        placeholder = st.empty()
        
        # Inyectamos el círculo giratorio de colores
        placeholder.markdown("""
            <div class="thinking-text">
                <div class="gemini-loader"></div>
                &nbsp;&nbsp;Zeo está pensando...
            </div>
        """, unsafe_allow_html=True)

        # 3. Lógica del Cerebro (Mientra la animación gira)
        full_res = "..."
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
        
        # 4. Limpiamos la animación y mostramos el texto real
        placeholder.empty()
        st.markdown(full_res)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_log("ZEO", full_res)
