import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import os

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="ZEO SYSTEM", page_icon="⚖️", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #E3E3E3; }
    .stChatMessage { border-radius: 15px; border: 1px solid #333; background-color: #0A0A0A; }
    [data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LLAVES ---
CLAVE_GEMINI = "AIzaSyAq2KiDVDhP4qdzRhEbotIY-BKc1fkFrXM"
genai.configure(api_key=CLAVE_GEMINI)

CLAVE_GROK = "xai-RL9UkICSk9qoMM84JYmswmm96u6huidymni2HLMnthr1X7e29xDK1DtpkpmMb9wotO5688jt7o3Ia7xf"
client_grok = OpenAI(api_key=CLAVE_GROK, base_url="https://api.x.ai/v1")

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

# --- 4. INICIALIZACIÓN (LISTA EXACTA DE TU ZEO.PY) ---
def iniciar_chat_diagnostico():
    # USAMOS EXACTAMENTE TU LISTA + BACKUPS
    modelos_a_probar = [
        "gemini-2.5-pro",       # Tu script usa este primero
        "gemini-pro-latest",    # Tu script usa este segundo
        "gemini-3-pro-preview", # Tu script usa este tercero
        "gemini-1.5-pro",       # Estándar
        "gemini-pro"            # Clásico
    ]
    
    reporte_errores = []

    for nombre in modelos_a_probar:
        try:
            test = genai.GenerativeModel(nombre)
            # Intentamos generar algo simple para ver si conecta
            test.generate_content("ping")
            
            # Si pasa el ping, iniciamos el chat CON MEMORIA (Tu método)
            chat = test.start_chat(history=[
                {"role": "user", "parts": [PROMPT_ZEO]},
                {"role": "model", "parts": ["ZEO online. Mayordomo listo. ¿En qué le sirvo, Sr. Eliot?"]}
            ])
            return chat, f"Conectado a: {nombre}"
        except Exception as e:
            reporte_errores.append(f"{nombre}: {str(e)}")
            continue
    
    return None, reporte_errores

if "chat_session" not in st.session_state:
    chat, info = iniciar_chat_diagnostico()
    st.session_state.chat_session = chat
    st.session_state.debug_info = info
    st.session_state.messages = []

# --- 5. INTERFAZ ---
st.title("⚖️ ZEO SYSTEM")

# Si falló la conexión, mostramos EL ERROR REAL en pantalla
if st.session_state.chat_session is None:
    st.error("⚠️ FALLO TOTAL DE CONEXIÓN. Aquí está el reporte técnico:")
    st.code(str(st.session_state.debug_info))
    st.stop() # Detiene la app aquí para que leas el error

with st.sidebar:
    st.header("Multimedia")
    st.caption(f"Motor: {st.session_state.debug_info}") # Para que sepas cuál cargó
    archivo = st.file_uploader("Subir evidencia", type=['png', 'jpg', 'jpeg'])
    if st.button("Reiniciar ZEO"):
        st.session_state.chat_session = None
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. LÓGICA DE RESPUESTA ---
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
            except Exception as e: full_res = f"ZEOX Error: {e}"
        else:
            if st.session_state.chat_session:
                try:
                    if archivo:
                        img = Image.open(archivo)
                        # Truco para visión sin romper el historial de texto
                        visor = genai.GenerativeModel("gemini-1.5-pro")
                        response = visor.generate_content([PROMPT_ZEO + "\n" + prompt, img])
                        full_res = response.text
                    else:
                        response = st.session_state.chat_session.send_message(prompt)
                        full_res = response.text
                except Exception as e:
                    full_res = f"⚠️ ZEO ha tropezado: {e}"
            else:
                full_res = "⚠️ ERROR: No hay cerebro conectado."

        st.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})