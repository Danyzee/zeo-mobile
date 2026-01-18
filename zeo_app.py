import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="ZEO RADAR", page_icon="📡", layout="centered")
st.title("📡 ZEO RADAR: Escaneando Modelos")

# 1. CONFIGURAR LLAVE
try:
    if "CLAVE_GEMINI" in st.secrets:
        genai.configure(api_key=st.secrets["CLAVE_GEMINI"])
        st.success("✅ Clave detectada. Consultando a Google...")
    else:
        st.error("❌ Falta CLAVE_GEMINI en Secrets")
        st.stop()
except Exception as e:
    st.error(f"❌ Error Config: {e}")
    st.stop()

# 2. LISTAR MODELOS REALES
st.write("---")
st.subheader("📋 LISTA OFICIAL DE TU CUENTA:")

try:
    # Preguntamos a la API qué modelos ve TU llave
    modelos_disponibles = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            nombre = m.name
            st.code(nombre) # Muestra el nombre exacto (ej: models/gemini-1.5-pro)
            modelos_disponibles.append(nombre)
            
    if not modelos_disponibles:
        st.warning("⚠️ Tu llave conecta, pero Google dice que NO tienes acceso a ningún modelo. (Posible bloqueo regional o de facturación).")
    else:
        st.success(f"✅ Se encontraron {len(modelos_disponibles)} modelos disponibles.")

except Exception as e:
    st.error(f"❌ Error al listar modelos: {e}")
    st.write("Pista: Si sale error 400/403 aquí, tu clave no tiene permisos para 'ListModels'.")

# 3. VERIFICAR LIBRERÍA
st.write("---")
st.caption(f"Versión de librería instalada: {genai.__version__}")
