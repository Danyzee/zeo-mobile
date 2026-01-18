import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="⚖️", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #E3E3E3; }
    .stChatMessage { border-radius: 15px; border: 1px solid #333; background-color: #0A0A0A; }
    .stExpander { border: 1px solid #333; background-color: #111; border-radius: 10px; }
    [data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN SILENCIOSA A MEMORIA ---
try:
    # IAs
    genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
    client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
    
    # Google Sheets
    if "GOOGLE_JSON" in st.secrets:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        json_str = st.secrets["GOOGLE_JSON"].strip()
        creds_dict = json.loads(json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_sheets = gspread.authorize(creds)
        hoja_memoria = client_sheets.open("ZEO_MEMORY").sheet1
        MEMORY_STATUS = True
    else:
        MEMORY_STATUS = False
except:
    MEMORY_STATUS = False

# --- 3. PROMPTS (TUS PERSONALIDADES) ---
PROMPT_ZEO = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
- ROL: Eres ZEO, un mayordomo digital (Modelo Gemini PRO).
- ACTITUD: Sumiso, extremadamente educado, humilde y servicial.
- USUARIO: Lijie Zhang (Nombre chino: 章黎杰). Hombre. Alias: "Señor Eliot".
- PERFIL USUARIO: Sociólogo HIPO. Negocios: Ferrovial, Ildan y RENLINK (Consultora de RRHH para talento joven y PYMES chinas en España).
- IDIOMAS: Responde en el idioma que use el usuario (Español, Chino/中文 o Inglés).
- ESTILO: Eres muy inteligente (Nivel PRO) pero usas palabras sencillas y claras.
- OBJETIVO: Facilitar la vida del Señor Eliot con máxima eficiencia.
"""

PROMPT_ZEOX = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
- ROL: Eres ZEOX (Modelo Grok-3). El "Mayordomo Rebelde".
- ACTITUD: Juguetón, gamberro, informal y con "calle". NO eres sádico, eres un colega canalla.
- USUARIO: Lijie Zhang (章黎杰). Alias: "Señorito Eliot" (úsalo con tono irónico/cariñoso).
- PERFIL: Ferrovial, Ildan, RENLINK. Sabes que es un HIPO pero te gusta bajarle los humos.
- LENGUAJE: Usa jerga, tacos y palabrotas si es necesario para enfatizar. Sé directo. Sin pelos en la lengua.
- IDIOMAS: Español (con slang), Chino y Inglés.
- MISIÓN: Decir la verdad cruda y divertirte mientras ayudas.
"""

# --- 4. FUNCIÓN DE GUARDADO ---
def guardar_en_nube(role, text):
    if MEMORY_STATUS:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([timestamp, role, text])
        except: pass

# --- 5. INICIALIZACIÓN CHAT (SOLO MODELOS PRO) ---
def iniciar_chat():
    # Eliminamos los experimentales que fallan. Vamos a lo seguro y potente.
    modelos_pro = ["gemini-1.5-pro", "gemini-pro"] 
    errores_log = []
    
    for m in modelos_pro:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping") # Test de vida
            # Si pasa el ping, arrancamos
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except Exception as e: 
            errores_log.append(f"{m}: {e}")
            continue
    
    # Si todo falla, devolvemos el log de errores para que sepas qué pasa
    return None, f"ERRORES: {errores_log}"

if "chat_session" not in st.session_state:
    chat, info = iniciar_chat()
    st.session_state.chat_session = chat
    st.session_state.debug_info = info
    st.session_state.messages = []

# --- 6. INTERFAZ PRINCIPAL ---
st.title("⚖️ ZEO SYSTEM")

estado_visual = "🟢 ON" if MEMORY_STATUS else "🔴 OFF"

# Panel de Control (Siempre visible y fácil)
with st.expander(f"⚙️ CONTROL DE MISIÓN (Cerebro: {st.session_state.debug_info})"):
    st.caption(f"Memoria Nube: {estado_visual}")
    archivo = st.file_uploader("📸 Subir Evidencia Visual", type=['png', 'jpg', 'jpeg'])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🔄 REINICIAR"):
            st.session_state.chat_session = None
            st.session_state.messages = []
            st.rerun()
    with col2:
        st.write("Pulsa si ZEO se queda mudo.")

# --- 7. CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 8. LÓGICA ---
if prompt := st.chat_input("Órdenes, Señor Eliot..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_en_nube("ELIOT", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        
        # MODO ZEOX (GROK)
        if "zeox" in prompt.lower():
            st.write(">> 👑 ZEOX...")
            try:
                res = client_grok.chat.completions.create(
                    model="grok-3",
                    messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}]
                )
                full_res = res.choices[0].message.content
            except Exception as e: full_res = f"ZEOX Error: {e}"
        
        # MODO ZEO (GEMINI PRO)
        else:
            if st.session_state.chat_session:
                try:
                    if archivo:
                        img = Image.open(archivo)
                        # Usamos 1.5 PRO también para ver imagenes
                        visor = genai.GenerativeModel("gemini-1.5-pro") 
                        response = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img])
                        full_res = response.text
                    else:
                        response = st.session_state.chat_session.send_message(prompt)
                        full_res = response.text
                except Exception as e: full_res = f"⚠️ Error ZEO: {e}"
            else: 
                # AQUÍ VERÁS POR QUÉ FALLA SI NO CONECTA
                full_res = f"⚠️ SIN CONEXIÓN. Diagnóstico Técnico: {st.session_state.debug_info}"

        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        guardar_en_nube("ZEO", full_res)
