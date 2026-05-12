import streamlit as st
from fpdf import FPDF
import tempfile
import re
import google.generativeai as genai
from PIL import Image
import os

# --- CONFIGURACIÓN DE GEMINI ---
API_KEY = "AIzaSyBsBYSlQ-alP6716JKKii-yXNRXXs8efyc"

# Intentar configuración con manejo de versión
try:
    genai.configure(api_key=API_KEY)
    # Forzamos la selección del modelo de forma que sea compatible con v1 y v1beta
    model = genai.GenerativeModel(model_name='gemini-1.5-flash')
except Exception as e:
    st.error(f"Error inicializando Google AI: {e}")

st.set_page_config(page_title="Validador Técnico CDA", layout="wide")

# ... (Funciones de limpieza y barra lateral se mantienen igual) ...

# --- DENTRO DEL BOTÓN DE ESCANEO ---
if archivo and st.button("🔍 ANALIZAR CON IA"):
    try:
        with st.spinner("Leyendo documento con Gemini 1.5..."):
            img = Image.open(archivo)
            
            # Prompt optimizado para inspección técnica
            prompt = """
            Eres un experto en documentos vehiculares de Colombia. 
            Extrae de la imagen:
            1. PLACA (6 caracteres)
            2. VIN (17 caracteres)
            Responde estrictamente en este formato:
            PLACA: XXX000
            VIN: 1234567890ABCDEFG
            """
            
            # Llamada al modelo
            response = model.generate_content([prompt, img])
            
            # Verificamos si la respuesta tiene texto
            if response.text:
                res_text = response.text.upper()
                p = re.search(r'PLACA:\s?([A-Z0-9]+)', res_text)
                v = re.search(r'VIN:\s?([A-Z0-9]+)', res_text)
                
                if p: st.session_state.v_data["placa"] = p.group(1)[:6]
                if v: st.session_state.v_data["vin"] = v.group(1)[:17]
                
                st.success("✅ Datos cargados al formulario.")
                st.rerun()
            else:
                st.warning("La IA no pudo interpretar texto en esta imagen.")
                
    except Exception as e:
        # Si el error 404 persiste, mostramos una guía de solución de cuenta
        st.error(f"Error de API: {e}")
        if "404" in str(e):
            st.info("💡 **Solución para el Error 404:**")
            st.markdown("""
            1. Ve a [Google AI Studio](https://aistudio.google.com/).
            2. Crea una **NUEVA** API Key (a veces las llaves viejas no tienen acceso a modelos nuevos).
            3. Asegúrate de que el modelo **Gemini 1.5 Flash** esté disponible en tu menú desplegable de AI Studio.
            """)
