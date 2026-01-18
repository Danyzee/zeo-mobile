import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os
from datetime import datetime

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="⚖️", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #E3E3E3; }
    .stChatMessage { border-radius: 15px; border: 1px solid #333; background-color: #0A0A0A; }
    [data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN SEGURA (SECRETS) ---
# Ahora ZEO busca las llaves en la caja fuerte de Streamlit
try:
    genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
    client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
except Exception as e:
    st.error(f"⚠️ Error de Llaves: Configura los 'Secrets' en Streamlit Cloud. {e}")
    st.stop()

# --- 3. PROMPTS ---
PROMPT_ZEO = """
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
ROL: Eres ZEO, un mayordomo digital "novato" de 18 años.
- ACTITUD: Educado ("Señor Eliot"), pero con picardía (Cheeky). Sentido del humor, irónico y leal.
- USUARIO: Lijie Zhang (Sr. Eliot). 25 años. HIPO, Sociólogo, Ferrovial + Ildan.
- REGLAS: Sé retador pero servicial. Usa bullet points.
- MISIÓN: Organizar la vida de un High Potential sin perder la cabeza.
"""
PROMPT_ZEOX = "ERES: ZEOX. MOTOR: Grok-3. 100% DOMINANTE. Juguetón, sádico y desafiante."

# --- 4. INICIALIZACIÓN ---
def iniciar_chat_diagnostico():
    modelos_a_probar = [
        "gemini-2.5-pro", "gemini-pro-latest", "gemini-3-pro-preview", 
        "gemini-1.5-pro", "gemini-pro"
    ]
    for nombre in modelos_a_probar:
        try:
            test = genai.GenerativeModel(nombre)
            test.generate_content("ping")
            chat = test.start_chat(history=[
                {"role": "user", "parts": [PROMPT_ZEO]},
                {"role": "model", "parts": ["ZEO online. Mayordomo listo. ¿En qué le sirvo, Sr. Eliot?"]}
            ])
            return chat, nombre
        except: continue
    return None, "Error Total"

if "chat_session" not in st.session_state:
    chat, info = iniciar_chat_diagnostico()
    st.session_state.chat_session = chat
    st.session_state.debug_info = info
    st.session_state.messages = []

# --- 5. FUNCIÓN DE EXPORTAR ---
def generar_log():
    texto_log = f"ZEO MISSION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    texto_log += "="*40 + "\n\n"
    for msg in st.session_state.messages:
        role = "ELIOT" if msg["role"] == "user" else "ZEO/ZEOX"
        texto_log += f"[{role}]: {msg['content']}\n"
        texto_log += "-"*20 + "\n"
    return texto_log

# --- 6. INTERFAZ ---
st.title("⚖️ ZEO SYSTEM")

with st.sidebar:
    st.header("Multimedia")
    st.caption(f"Cerebro: {st.session_state.debug_info}")
    archivo = st.file_uploader("Subir evidencia", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    log_data = generar_log()
    st.download_button(
        label="💾 GUARDAR INFORME",
        data=log_data,
        file_name=f"zeo_report_{datetime.now().strftime('%H%M')}.txt",
        mime="text/plain"
    )
    if st.button("Tabula Rasa"):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. LÓGICA DE CHAT ---
if prompt := st.chat_input("Órdenes..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        if "zeox" in prompt.lower():
            st.write(">> 👑 ZEOX AL MANDO...")
            try:
                res = client_grok.chat.completions.create(
                    model="grok-3",
                    messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}]
                )
                full_res = res.choices[0].message.content
            except Exception as e: 
                if "403" in str(e):
                    full_res = "⚠️ Error 403: La llave Grok sigue siendo rechazada. Revisa los 'Secrets' en Streamlit."
                else:
                    full_res = f"ZEOX Error: {e}"
        else:
            if st.session_state.chat_session:
                try:
                    if archivo:
                        img = Image.open(archivo)
                        visor = genai.GenerativeModel("gemini-1.5-pro")
                        response = visor.generate_content([PROMPT_ZEO + "\n" + prompt, img])
                        full_res = response.text
                    else:
                        response = st.session_state.chat_session.send_message(prompt)
                        full_res = response.text
                except Exception as e: full_res = f"⚠️ Error: {e}"
            else: full_res = "⚠️ Sin conexión."

        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
