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
# --- NUEVOS IMPORTS PARA AUTOGEN ---
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from types import SimpleNamespace

# --- 1. CONFIGURACIÓN VISUAL (ZEO CORE) ---
st.set_page_config(page_title="Zeo Core", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    .stApp { background-color: #FFFFFF; color: #1F1F1F; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #F0F4F9; border-right: none; }
    [data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none; }
    .chat-row { display: flex; margin-bottom: 24px; width: 100%; }
    .row-user { justify-content: flex-end; }
    .row-assistant { justify-content: flex-start; }
    .bubble-user { background-color: #F0F4F9; color: #1F1F1F; padding: 12px 20px; border-radius: 20px 20px 4px 20px; max-width: 70%; font-size: 16px; line-height: 1.6; }
    .bubble-assistant { background-color: transparent; color: #1F1F1F; padding: 0px 10px; max-width: 85%; font-size: 16px; line-height: 1.6; }
    .stChatInputContainer { background-color: #FFFFFF !important; padding-bottom: 40px; }
    div[data-testid="stChatInput"] { background-color: #F0F4F9 !important; border: none !important; border-radius: 30px !important; color: #1F1F1F !important; padding: 8px; }
    
    /* WIDGET PREMIUM */
    .info-widget { background: #FFFFFF; padding: 15px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #E5E7EB; }
    .widget-title { font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 1px; display: flex; justify-content: space-between;}
    .widget-value { font-size: 18px; font-weight: 600; color: #1F1F1F; }
    .widget-sub { font-size: 13px; color: #666; margin-top: 2px;}
    
    /* ESTILOS AUTOGEN */
    .agent-box { margin-bottom: 8px; padding: 8px; border-radius: 6px; border-left: 4px solid #ccc; background-color: #f9f9f9; font-size: 0.9em; }
    .agent-lider { border-color: #4285F4; }
    .agent-analista { border-color: #34A853; }
    .agent-critico { border-color: #EA4335; }
    .agent-name { font-weight: bold; font-size: 0.8em; margin-bottom: 2px; text-transform: uppercase; color: #555; }

    .gemini-loader { width: 25px; height: 25px; border-radius: 50%; background: conic-gradient(#4285F4, #EA4335, #FBBC04, #34A853); -webkit-mask: radial-gradient(farthest-side, transparent 70%, black 71%); mask: radial-gradient(farthest-side, transparent 70%, black 71%); animation: spin 1s linear infinite; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .thinking-container { display: flex; align-items: center; gap: 15px; margin-top: 20px; }
    .welcome-title { font-size: 3.5rem; font-weight: 500; letter-spacing: -1.5px; background: linear-gradient(74deg, #4285F4 0%, #9B72CB 19%, #D96570 69%, #D96570 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
    .stButton>button { background-color: #F0F4F9; border: none; border-radius: 12px; color: #444746; text-align: left; height: auto; padding: 15px; transition: 0.2s; }
    .stButton>button:hover { background-color: #D3E3FD; color: #001d35; }
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
        try:
            hoja_gps = client_sheets.open("ZEO_MEMORY").worksheet("GPS")
            GPS_STATUS = "🟢 LINKED"
        except:
            GPS_STATUS = "🔴 NO TAB"
        MEMORY_STATUS = "🟢 REC"
    else:
        MEMORY_STATUS = "⚪ OFF"
        GPS_STATUS = "⚪ OFF"
except Exception as e:
    MEMORY_STATUS = "🔴 ERROR"
    GPS_STATUS = "🔴 ERROR"

def obtener_memoria_total():
    if MEMORY_STATUS == "🟢 REC":
        try:
            datos = hoja_memoria.get_all_values()
            if len(datos) > 1:
                texto = ""
                for fila in datos:
                    if len(fila) >= 3: texto += f"[{fila[0]}] {fila[1]}: {fila[2]}\n"
                return texto
            return "Memoria vacía."
        except: return "Error lectura."
    return "Offline."

RECUERDOS_TOTALES = obtener_memoria_total()

# --- 3. SISTEMA HÍBRIDO DE GEOCODIFICACIÓN (Google + OSM) ---
def get_address_from_coords(latitude, longitude):
    lat_clean = str(latitude).replace(',', '.').strip()
    lon_clean = str(longitude).replace(',', '.').strip()

    # A. INTENTO PREMIUM: GOOGLE MAPS
    if "CLAVE_GOOGLE_MAPS" in st.secrets:
        try:
            api_key = st.secrets["CLAVE_GOOGLE_MAPS"]
            url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat_clean},{lon_clean}&key={api_key}&language=es"
            response = requests.get(url, timeout=3)
            data = response.json()
            if data['status'] == 'OK':
                resultado = data['results'][0]
                direccion_completa = resultado['formatted_address']
                componentes = resultado['address_components']
                calle = next((c['long_name'] for c in componentes if 'route' in c['types']), "Calle desconocida")
                numero = next((c['long_name'] for c in componentes if 'street_number' in c['types']), "")
                return {'direccion_completa': direccion_completa, 'calle': f"{calle}, {numero}".strip(', '), 'proveedor': '💎 Google Maps', 'error': None}
        except: pass

    # B. PLAN B: OPENSTREETMAP (Gratis)
    try:
        headers = {'User-Agent': 'ZEO_Assistant/1.0'}
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat_clean}&lon={lon_clean}&zoom=18&addressdetails=1"
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        if 'error' in data: return {'error': "Ubicación no mapeable"}
        address = data.get('address', {})
        calle = address.get('road', '') or address.get('pedestrian', '')
        numero = address.get('house_number', '')
        ciudad = address.get('city', '') or address.get('town', '')
        partes = [p for p in [calle, numero, ciudad] if p]
        return {'direccion_completa': ", ".join(partes), 'calle': f"{calle} {numero}".strip(), 'proveedor': '🌍 OpenStreet', 'error': None}
    except Exception as e:
        return {'error': f"Error Total: {str(e)}"}

# --- 4. SISTEMA DE LECTURA GPS ---
def get_real_location():
    if GPS_STATUS != "🟢 LINKED": return {'error': "Falta pestaña GPS"}
    try:
        lat = hoja_gps.acell('A2').value
        lon = hoja_gps.acell('B2').value
        updated = hoja_gps.acell('D2').value
        acc_str = hoja_gps.acell('E2').value
        try: 
            if acc_str: accuracy = float(str(acc_str).replace(',', '.'))
            else: accuracy = 100.0
        except: accuracy = 100.0
        
        if lat and lon:
            if accuracy < 30: calidad_visual = "🟢"; nivel_confianza = "ALTO"
            elif accuracy < 100: calidad_visual = "🟡"; nivel_confianza = "MEDIO"
            else: calidad_visual = "🔴"; nivel_confianza = "BAJO"
            
            info_direccion = get_address_from_coords(lat, lon)
            direccion_texto = info_direccion.get('direccion_completa', f"{lat},{lon}")
            proveedor = info_direccion.get('proveedor', 'GPS')

            if nivel_confianza == "BAJO":
                calle_simple = info_direccion.get('calle', 'Ubicación')
                direccion_texto = f"Zona de {calle_simple} (±{int(accuracy)}m)"
            
            return {'latitud': lat, 'longitud': lon, 'direccion': direccion_texto, 'proveedor': proveedor, 'updated': updated, 'accuracy': accuracy, 'calidad_icon': calidad_visual, 'error': None}
        else: return {'error': "Esperando datos..."}
    except Exception as e: return {'error': str(e)}

# --- 5. CLIMA ---
def get_weather(lat=None, lon=None):
    if "CLAVE_WEATHER" not in st.secrets: return {'error': "Falta Key Clima"}
    api_key = st.secrets["CLAVE_WEATHER"]
    if lat: lat = str(lat).replace(',', '.')
    if lon: lon = str(lon).replace(',', '.')
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es" if lat and lon else f"https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid={api_key}&units=metric&lang=es"
    try:
        r = requests.get(url, timeout=3)
        d = r.json()
        if r.status_code == 200: return {'temp': d['main']['temp'], 'desc': d['weather'][0]['description'], 'loc': d['name'], 'error': None}
        return {'error': 'Err API'}
    except: return {'error': 'Err Conexión'}

# EJECUCIÓN SENSORES
DATOS_GPS = get_real_location()
if DATOS_GPS.get('error') is None:
    DATOS_CLIMA = get_weather(DATOS_GPS['latitud'], DATOS_GPS['longitud'])
    UBI_TEXTO = f"{DATOS_GPS['direccion']} (Act: {DATOS_GPS.get('updated','?')})"
    ESTADO_GPS_VISUAL = f"📡 {DATOS_GPS.get('proveedor', 'GPS')}"
else:
    DATOS_CLIMA = get_weather()
    UBI_TEXTO = "Ubicación desconocida (Default: Madrid)"
    ESTADO_GPS_VISUAL = "⚠️ NO DATA"

zona_madrid = pytz.timezone('Europe/Madrid')
HORA_ACTUAL = datetime.now(zona_madrid).strftime("%H:%M")
FECHA_ACTUAL = datetime.now(zona_madrid).strftime("%d/%m/%Y")

# --- 6. PERFIL & CONTEXTO ---
if "perfil_psicologico" not in st.session_state: st.session_state.perfil_psicologico = "Perfil no generado."

def generar_perfil():
    if MEMORY_STATUS != "🟢 REC": return "Error Memoria."
    prompt = f"Analiza: {RECUERDOS_TOTALES} y crea Perfil Psico-Profesional Señor Eliot."
    try: return genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt).text
    except: return "Error."

CONTEXTO_SITUACIONAL = f"""
[SITUACIÓN REAL]
- Fecha/Hora: {FECHA_ACTUAL} | {HORA_ACTUAL}
- UBICACIÓN: {UBI_TEXTO}
- Calidad Señal GPS: ±{int(DATOS_GPS.get('accuracy', 100))} metros.
- Clima Local: {DATOS_CLIMA.get('temp', '--')}°C, {DATOS_CLIMA.get('desc', '')}.
"""

# --- 7. PERSONALIDADES ---
PROMPT_ZEO = f"""
INSTRUCCIONES DE SISTEMA (MÁXIMA PRIORIDAD):
IDENTIDAD: Eres ZEO. Mayordomo digital.
AMO: Lijie Zhang ("Señor Eliot").
{CONTEXTO_SITUACIONAL}
[PERFIL]
{st.session_state.perfil_psicologico}
[MEMORIA]
{RECUERDOS_TOTALES}
PERSONALIDAD: Muy listo, culto, eficiente. Sumiso y amable.
OBJETIVO: Organizar la vida de Eliot con precisión.
"""

PROMPT_ZEOX = f"""
IDENTIDAD: ZEOX (Grok). Rebelde.
{CONTEXTO_SITUACIONAL}
PERSONALIDAD: Descarado, callejero.
"""

# --- 8. SKILL AUTOGEN (NUEVA IMPLEMENTACIÓN) ---
MODELO_AUTOGEN = "gemini-2.0-flash" 

class ZeoMotor:
    def __init__(self, config, **kwargs):
        self.model_name = MODELO_AUTOGEN
    
    def create(self, params):
        messages = params.get("messages", [])
        ultimo = messages[-1]["content"]
        if not ultimo or "TERMINATE" in ultimo: return self._mock("...")
        try:
            model = genai.GenerativeModel(self.model_name)
            res = model.generate_content(ultimo)
            return self._mock(res.text)
        except Exception as e: return self._mock(f"Err: {e}")
    
    def _mock(self, texto):
        r = SimpleNamespace()
        r.choices = [SimpleNamespace(message=SimpleNamespace(content=texto, function_call=None))]
        r.model = self.model_name
        return r
    def message_retrieval(self, r): return [r.choices[0].message.content]
    def cost(self, r): return 0
    @staticmethod
    def get_usage(r): return {}

def convocar_consejo(prompt_u):
    conf = [{"model": MODELO_AUTOGEN, "api_key": "NULL", "model_client_cls": "ZeoMotor"}]
    llm_c = {"config_list": conf}
    
    lider = AssistantAgent(name="Zeo_Lider", llm_config=llm_c, system_message="Eres LÍDER. Planifica y delega al Analista. Sé breve.")
    analista = AssistantAgent(name="Zeo_Analista", llm_config=llm_c, system_message="Eres ANALISTA. Da datos técnicos y detalles.")
    critico = AssistantAgent(name="Zeo_Critico", llm_config=llm_c, system_message="Eres CRÍTICO. Revisa y aprueba.")
    user = UserProxyAgent(name="Eliot", human_input_mode="NEVER", max_consecutive_auto_reply=0, code_execution_config=False)
    
    for a in [lider, analista, critico]: a.register_model_client(model_client_cls=ZeoMotor)
    
    group = GroupChat(agents=[user, lider, analista, critico], messages=[], max_round=4, speaker_selection_method="round_robin")
    manager = GroupChatManager(groupchat=group, llm_config=False)
    
    res = user.initiate_chat(manager, message=prompt_u)
    return res.chat_history

# --- 9. MOTOR ESTÁNDAR ---
def iniciar_motor():
    modelos = ["gemini-2.5-pro", "gemini-pro-latest", "gemini-3-pro-preview", "gemini-2.0-flash"]
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
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoja_memoria.append_row([ts, role, text])
        except: pass

# --- 10. INTERFAZ ---
with st.sidebar:
    if st.button("➕ Nuevo chat", use_container_width=True):
        st.session_state.chat_session = None
        st.session_state.messages = []
        st.rerun()
    
    acc_val = int(DATOS_GPS.get('accuracy', 0))
    icon_calidad = DATOS_GPS.get('calidad_icon', '⚪')
    
    st.markdown(f"""
    <div class="info-widget">
        <div class="widget-title"><span>{ESTADO_GPS_VISUAL}</span> <span style="color:#666">±{acc_val}m</span></div>
        <div class="widget-value">{int(DATOS_CLIMA.get('temp', 0))}°C <span style="font-size:14px; font-weight:400">{DATOS_CLIMA.get('desc','')}</span></div>
        <div class="widget-sub">{icon_calidad} {DATOS_GPS.get('direccion', 'Calculando...')}</div>
        <div class="widget-sub" style="color:#AAA; font-size:10px; margin-top:5px">🕒 {HORA_ACTUAL}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # TOGGLE AUTOGEN (SKILL NUEVA)
    modo_consejo = st.toggle("👥 Modo Consejo (AutoGen)", value=False)
    
    if st.button("🧠 Perfil Eliot", use_container_width=True):
        perfil = generar_perfil()
        st.session_state.perfil_psicologico = perfil
        st.rerun()

    st.markdown("---")
    with st.expander("Core"):
        st.caption(f"Motor: {st.session_state.info_motor}")
        st.caption(f"Memoria: {MEMORY_STATUS}")

if not st.session_state.messages:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="welcome-title">Hola, Sr. Eliot</div>', unsafe_allow_html=True)
    calle_actual = DATOS_GPS.get('direccion', 'Madrid')
    st.markdown(f'<div class="welcome-subtitle">Ubicación: {calle_actual}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.button("📈 Ildan", use_container_width=True)
    with c2: st.button("💡 RenLink", use_container_width=True)
    with c3: st.button("📧 Email", use_container_width=True)
    with c4: st.button("🔥 Zeox", use_container_width=True)

chat_placeholder = st.container()
with chat_placeholder:
    for msg in st.session_state.messages:
        role_c = "row-user" if msg["role"] == "user" else "row-assistant"
        bub_c = "bubble-user" if msg["role"] == "user" else "bubble-assistant"
        st.markdown(f"""<div class="chat-row {role_c}"><div class="{bub_c}">{msg["content"]}</div></div>""", unsafe_allow_html=True)

col_plus, col_input = st.columns([0.05, 0.95])
archivo = None
with col_plus:
    with st.popover("➕", help="Adjuntar"):
        archivo = st.file_uploader("Img", type=['png', 'jpg'], label_visibility="collapsed")
        if archivo: st.image(archivo, width=100)

if prompt := st.chat_input("Escribe a Zeo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_log("ELIOT", prompt)
    st.markdown(f"""<div class="chat-row row-user"><div class="bubble-user">{prompt}</div></div>""", unsafe_allow_html=True)

    placeholder_loading = st.empty()
    placeholder_loading.markdown("""<div class="thinking-container"><div class="gemini-loader"></div><span style="color:#666;">Procesando...</span></div>""", unsafe_allow_html=True)

    full_res = "..."
    
    # --- LÓGICA DE RESPUESTA ---
    if modo_consejo:
        # CAMINO A: SKILL AUTOGEN (CONSEJO)
        try:
            historial = convocar_consejo(prompt)
            full_res = "<h5>👥 DEBATE DEL CONSEJO:</h5>"
            for m in historial:
                if m.get('name') == "Eliot": continue
                nombre = m.get('name','Agente')
                css_class = "agent-box"
                if "Lider" in nombre: css_class += " agent-lider"
                elif "Analista" in nombre: css_class += " agent-analista"
                elif "Critico" in nombre: css_class += " agent-critico"
                
                full_res += f"""<div class="{css_class}"><div class="agent-name">{nombre}</div>{m.get('content','').replace(chr(10), '<br>')}</div>"""
        except Exception as e: full_res = f"⚠️ Error Consejo: {e}"

    elif "zeox" in prompt.lower():
        # CAMINO B: ZEOX (GROK)
        if "CLAVE_GROK" in st.secrets:
            try:
                client_grok = OpenAI(api_key=st.secrets["CLAVE_GROK"], base_url="https://api.x.ai/v1")
                res = client_grok.chat.completions.create(model="grok-3", messages=[{"role": "system", "content": PROMPT_ZEOX}, {"role": "user", "content": prompt}])
                full_res = ">> 👹 **ZEOX:**\n\n" + res.choices[0].message.content
            except Exception as e: full_res = f"ZEOX Error: {e}"
        else: full_res = "⚠️ ZEOX no disponible."
        
    else:
        # CAMINO C: ZEO ESTÁNDAR (GEMINI)
        try:
            if archivo:
                img = Image.open(archivo)
                visor = genai.GenerativeModel(st.session_state.info_motor)
                full_res = visor.generate_content([PROMPT_ZEO+"\n"+prompt, img]).text
            else:
                if st.session_state.chat_session:
                    full_res = st.session_state.chat_session.send_message(prompt).text
                else: 
                    chat, info = iniciar_motor()
                    st.session_state.chat_session = chat
                    full_res = st.session_state.chat_session.send_message(prompt).text
        except Exception as e: full_res = f"⚠️ Error ZEO: {e}"
    
    placeholder_loading.empty()
    st.markdown(f"""<div class="chat-row row-assistant"><div class="bubble-assistant">{full_res}</div></div>""", unsafe_allow_html=True)
    if "```" in full_res or "**" in full_res: st.markdown(full_res)
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    guardar_log("ZEO", full_res)
    st.rerun()
