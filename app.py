import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64
import easyocr
import numpy as np
from PIL import Image

# Inicializar el lector de OCR (Español e Inglés)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['es', 'en'])

reader = load_ocr()

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

st.set_page_config(page_title="Gestor con IA de Reclamaciones", layout="wide")

# --- LÓGICA DE PROCESAMIENTO DE IMAGEN ---
def procesar_imagen(uploaded_file):
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    resultado = reader.readtext(image_np, detail=0)
    texto_unido = " ".join(resultado).upper()
    return texto_unido

# --- BARRA LATERAL ---
st.sidebar.header("📝 Panel de Transcripción")

# Variables de estado para los campos
if 'datos_ocr' not in st.session_state:
    st.session_state.datos_ocr = {
        "placa": "KCM702",
        "nombre": "ADRIANA FERNANDEZ LOPEZ",
        "monto": "$ 5.467.111,00"
    }

with st.sidebar.expander("🚗 Datos del Vehículo", expanded=True):
    placa = st.text_input("Placa", value=st.session_state.datos_ocr["placa"], key="placa_ia")
    
with st.sidebar.expander("👤 Datos del Asegurado"):
    nombre = st.text_input("Nombre Completo", value=st.session_state.datos_ocr["nombre"], key="nombre_ia")

with st.sidebar.expander("📊 Reclamación"):
    monto = st.text_input("Monto", value=st.session_state.datos_ocr["monto"], key="monto_ia")

with st.sidebar.expander("🚦 Texto Extraído (Lectura de Imagen)"):
    # Aquí se mostrará todo lo que la IA leyó para que puedas copiar y pegar
    texto_detectado = st.text_area("Texto detectado por la IA:", height=200)

# --- CUERPO PRINCIPAL ---
st.markdown("<h2 style='text-align: center;'>🤖 Extracción Automática de Datos</h2>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📸 Sube aquí el pantallazo o foto para transcribir", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # PROCESAR CON OCR
    with st.spinner("Leyendo imagen..."):
        texto_extraido = procesar_imagen(uploaded_file)
        # Intentar detectar la placa automáticamente (ejemplo simple de 6 caracteres)
        import re
        placas_encontradas = re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', texto_extraido)
        
        if placas_encontradas:
            st.success(f"✅ Placa detectada: {placas_encontradas[0]}")
            # Aquí podrías actualizar el session_state si quisieras automatizar más
            
    st.image(uploaded_file, caption="Imagen procesada", width=400)
    
    # Mostrar el texto para que el usuario solo tenga que copiar/pegar lo que necesite
    st.info("👇 Abajo tienes todo el texto que la IA leyó de la imagen. Puedes copiarlo a los campos de la izquierda.")
    st.text_area("Resultado de la transcripción automática:", value=texto_extraido, height=150)

    if st.button("🚀 GENERAR PDF FINAL"):
        img_64 = base64.b64encode(uploaded_file.getvalue()).decode()
        # (Aquí va el resto de tu lógica de PDF que ya tenemos configurada)
        st.write("Generando documento con los datos de la izquierda...")
