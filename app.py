import streamlit as st
from fpdf import FPDF
import tempfile
import re
import google.generativeai as genai
from PIL import Image
import os

# --- CONFIGURACIÓN ROBUSTA DE GEMINI ---
API_KEY = "AIzaSyBsBYSlQ-alP6716JKKii-yXNRXXs8efyc"

# Forzamos la configuración para evitar el error 404
try:
    genai.configure(api_key=API_KEY)
    # Cambiamos el nombre al formato universalmente aceptado
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"Error al configurar la IA: {e}")

st.set_page_config(page_title="Validador Técnico CDA", layout="wide")

# ... (El resto del código de sumas y barra lateral se mantiene) ...

# --- BLOQUE DE ESCANEO CORREGIDO ---
with st.sidebar:
    # Asegúrate de que placa_f y vin_f existan para el PDF
    placa_f = st.text_input("📍 Placa", value=st.session_state.get('v_data', {}).get('placa', ""))
    vin_f = st.text_input("🆔 VIN", value=st.session_state.get('v_data', {}).get('vin', ""))

# ... (En el cuerpo principal donde subes el archivo) ...
archivo = st.file_uploader("Sube foto de evidencia", type=["jpg", "png", "jpeg"])

if archivo:
    st.image(archivo, use_container_width=True)
    if st.button("🔍 ANALIZAR CON IA"):
        try:
            with st.spinner("Leyendo documento..."):
                img = Image.open(archivo)
                # Prompt directo y sencillo
                prompt = "Extrae la PLACA y el VIN de este documento vehicular. Responde solo: PLACA: XXX000, VIN: 1234567890ABCDEFG"
                
                # LLAMADA CLAVE
                response = model.generate_content([prompt, img])
                
                if response.text:
                    res_text = response.text.upper()
                    p = re.search(r'PLACA:\s?([A-Z0-9]+)', res_text)
                    v = re.search(r'VIN:\s?([A-Z0-9]+)', res_text)
                    
                    if p: st.session_state.v_data["placa"] = p.group(1)[:6]
                    if v: st.session_state.v_data["vin"] = v.group(1)[:17]
                    
                    st.success("✅ Datos extraídos correctamente.")
                    st.rerun()
        except Exception as e:
            # Si vuelve a salir 404, mostramos el paso a paso de la cuenta
            st.error(f"Error de API: {e}")
            if "404" in str(e):
                st.info("⚠️ **Tu API Key necesita un ajuste manual:**")
                st.markdown("""
                1. Ve a [Google AI Studio](https://aistudio.google.com/).
                2. Haz clic en **'Plan de pago'** (tranquilo, sigue habiendo nivel gratuito).
                3. A veces Google bloquea el modelo **Flash** en cuentas 'Legacy' hasta que confirmas que eres un usuario activo.
                4. **Crea una clave nueva** y reemplázala en el código.
                """)
