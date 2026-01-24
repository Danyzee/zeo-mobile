import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- 1. CONFIGURACIÓN VISUAL (GEMINI LIGHT REPLICA) ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="✨", layout="wide")

# CSS: CLONACIÓN EXACTA DE GEMINI (MODO CLARO)
st.markdown("""
    <style>
    /* IMPORTAR FUENTE PARECIDA A GOOGLE SANS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* FONDO PRINCIPAL BLANCO PURO */
    .stApp { 
        background-color: #FFFFFF; 
        color: #1F1F1F; 
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR (GRIS PÁLIDO GEMINI) */
    [data-testid="stSidebar"] { 
        background-color: #F0F4F9; 
        border-right: none;
    }
    
    /* MENSAJES DE CHAT - LIMPIOS */
    .stChatMessage { background-color: transparent !important; border: none !important; }
    [data-testid="stChatMessage"] { padding: 1rem 0; }
    
    /* INPUT FLOTANTE (PILL SHAPE GRIS) */
    .stChatInputContainer {
        background-color: #FFFFFF !important;
        padding-bottom: 30px;
    }
    div[data-testid="stChatInput"] {
        background-color: #F0F4F9 !important; /* Gris Gemini */
        border: none !important;
        border-radius: 24px !important;
        color: #1F1F1F !important;
        padding: 5px;
    }
    div[data-testid="stChatInput"]:focus-within {
        background-color: #E9EEF6 !important; /* Ligeramente más oscuro al escribir */
        box-shadow: none !important;
    }
    
    /* BOTONES (TAGS) ESTILO GOOGLE */
    .stButton>button {
        background-color: #F0F4F9;
        color: #1F1F1F;
        border: none;
        border-radius: 12px;
        font-weight: 500;
        height: auto;
        padding: 10px 15px;
        text-align: left;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #D3E3FD; /* Azulito Google al pasar mouse */
        color: #041E49;
    }

    /* TEXTO DE BIENVENIDA CON DEGRADADO GEMINI */
    .welcome-text {
        font-size: 3.5rem;
        font-weight: 500;
        letter-spacing: -1px;
        background: linear-gradient(74deg, #4285F4 0%, #9B72CB 19%, #D96570 69%, #D96570 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    .welcome-sub {
        font-size: 3.5rem;
        font-weight: 500;
        letter-spacing: -1px;
        color: #C4C7C5; /* Gris claro para el texto secundario */
        line-height: 1.2;
    }

    /* OCULTAR ELEMENTOS EXTRAÑOS */
    [data-testid="stHeader"] { display: none; }
    [data-testid="stDecoration"] { display: none; }
    
    /* ICONO DE USUARIO Y ASISTENTE */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #F0F4F9;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN BLINDADA (TU NÚCLEO INTACTO) ---
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

# --- 3. PERSONALIDADES (TU ALMA DEL SISTEMA) ---
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

# --- 4. MOTOR INTELIGENTE (TU LISTA EXACTA CONSERVADA) ---
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

# --- 5. GUARDAR LOG ---
def guardar_log(role, text):
    if MEMORY_STATUS == "🟢 REC":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 6. INTERFAZ: REPLICA GEMINI UI ---

# A. SIDEBAR (GRIS PÁLIDO)
with st.sidebar:
    # Botón Nuevo Chat simulando el de Gemini (Gris)
    if st.button("➕ Nuevo chat", use_container_width=True):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### Recientes")
    st.caption("Hoy")
    st.markdown("☁️ *Previsión Madrid*")
    st.markdown("📊 *Informe RenLink*")
    
    st.markdown("---")
    # Indicadores técnicos discretos al fondo
    with st.expander("Ajustes"):
        st.caption(f"Motor: {st.session_state.info_motor}")
        st.caption(f"Memoria: {MEMORY_STATUS}")

# B. ÁREA PRINCIPAL (BLANCO PURO)
# Si es un chat nuevo, mostramos el saludo estilo Gemini con degradado
if not st.session_state.messages:
    # Espaciado superior para centrar
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="welcome-text">Hola, Sr. Eliot</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-sub">¿Cómo puedo ayudarle hoy?</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tarjetas de sugerencia (Gris Gemini)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.button("📈 Analizar Ildan", use_container_width=True)
    with c2: st.button("💡 Ideas RenLink", use_container_width=True)
    with c3: st.button("📧 Redactar mail", use_container_width=True)
    with c4: st.button("🔥 Modo ZEOX", use_container_width=True)

# C. CHAT
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# D. INPUT AREA (PILL SHAPE + HERRAMIENTAS)
col_plus, col_input = st.columns([0.05, 0.95])

archivo = None
with col_plus:
    # Botón "+" (Popover) limpio
    with st.popover("➕", help="Adjuntar"):
        st.caption("Herramientas")
        archivo = st.file_uploader("Subir imagen", type=['png', 'jpg'], label_visibility="collapsed")
        if archivo:
            st.success("Imagen lista")
            st.image(archivo, width=100)

if prompt := st.chat_input("Escribe una instrucción..."):
    # 1. User
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    with st.chat_message("user"): st.markdown(prompt)

    # 2. Assistant
    with st.chat_message("assistant"):
        full_res = "..."
        
        # MODO ZEOX (GROK)
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

        # MODO ZEO (GEMINI - NÚCLEO INTACTO)
        else:
            try:
                if archivo:
                    img = Image.open(archivo)
                    visor = genai.GenerativeModel(st.session_state.info_motor)
                    full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
                else:
                    if st.session_state.chat_session:
                        full_res = st.session_state.chat_session.send_message(prompt).text
                    else:
                        full_res = "⚠️ Error: Conexión perdida."
            except Exception as e: full_res = f"⚠️ Error ZEO: {e}"
        
        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_log("ZEO", full_res)
