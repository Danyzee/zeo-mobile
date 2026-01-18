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
    [data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN SEGURA (API KEYS + GOOGLE SHEETS) ---
try:
    # IAs
    genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
    client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
    
    # Google Sheets (Memoria Externa)
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(st.secrets["GOOGLE_JSON"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client_sheets = gspread.authorize(creds)
    hoja_memoria = client_sheets.open("ZEO_MEMORY").sheet1
    MEMORY_STATUS = "🟢 REC"
except Exception as e:
    MEMORY_STATUS = "🔴 OFF"
    # No detenemos la app, solo avisamos en silencio que no guardará
    print(f"Error de memoria: {e}")

# --- 3. PROMPTS ---
PROMPT_ZEO = """
INSTRUCCIONES: Eres ZEO. 18 años. Educado (Sr. Eliot) pero cheeky.
USUARIO: Lijie Zhang. HIPO.
MISIÓN: Organizar su vida. Sé breve y directo.
"""
PROMPT_ZEOX = "ERES: ZEOX. MOTOR: Grok-3. 100% DOMINANTE. Juguetón, sádico y desafiante."

# --- 4. FUNCIÓN DE GUARDADO AUTOMÁTICO ---
def guardar_en_nube(role, text):
    if MEMORY_STATUS == "🟢 REC":
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Escribimos: [FECHA, QUIEN, MENSAJE]
            hoja_memoria.append_row([timestamp, role, text])
        except:
            pass # Si falla internet, no molestamos al usuario

# --- 5. INICIALIZACIÓN CHAT ---
def iniciar_chat():
    modelos = ["gemini-2.5-pro", "gemini-pro-latest", "gemini-1.5-pro", "gemini-pro"]
    for m in modelos:
        try:
            test = genai.GenerativeModel(m)
            test.generate_content("ping")
            return test.start_chat(history=[{"role": "user", "parts": [PROMPT_ZEO]}]), m
        except: continue
    return None, "Error"

if "chat_session" not in st.session_state:
    chat, info = iniciar_chat()
    st.session_state.chat_session = chat
    st.session_state.debug_info = info
    st.session_state.messages = []

# --- 6. INTERFAZ ---
st.title("⚖️ ZEO SYSTEM")

with st.sidebar:
    st.header("Estado del Sistema")
    st.caption(f"Cerebro: {st.session_state.debug_info}")
    st.caption(f"Memoria Nube: {MEMORY_STATUS}")
    archivo = st.file_uploader("Evidencia", type=['png', 'jpg', 'jpeg'])
    if st.button("Tabula Rasa"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. LÓGICA DE RESPUESTA ---
if prompt := st.chat_input("Órdenes..."):
    # 1. Guardar Usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_en_nube("ELIOT", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        # MODO ZEOX
        if "zeox" in prompt.lower():
            st.write(">> 👑 ZEOX...")
            try:
                res = client_grok.chat.completions.create(
                    model="grok-3",
                    messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}]
                )
                full_res = res.choices[0].message.content
            except Exception as e: full_res = f"ZEOX Error: {e}"
        
        # MODO ZEO
        else:
            if st.session_state.chat_session:
                try:
                    if archivo:
                        img = Image.open(archivo)
                        visor = genai.GenerativeModel("gemini-1.5-pro")
                        response = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img])
                        full_res = response.text
                    else:
                        response = st.session_state.chat_session.send_message(prompt)
                        full_res = response.text
                except Exception as e: full_res = f"⚠️ Error: {e}"
            else: full_res = "⚠️ Sin conexión."

        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # 2. Guardar Robot
        guardar_en_nube("ZEO", full_res)})

