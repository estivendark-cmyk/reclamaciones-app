import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64
import easyocr
import numpy as np
from PIL import Image
import re

# Configuración de página
st.set_page_config(page_title="Validador IA de Siniestros", layout="wide")

# Motor de lectura IA
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['es'])

reader = load_ocr()

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

# --- LÓGICA DE EXTRACCIÓN INTELIGENTE ---
def extraer_datos_inteligentes(texto_lista):
    texto_unido = " ".join(texto_lista).upper()
    datos = {
        "nombre": "NO DETECTADO",
        "placa": "KCM702",
        "valor": "$ 0,00",
        "siniestro": "SIN REGISTRO"
    }
    
    # 1. Detectar Placa (Formato AAA000 o AAA00A)
    placas = re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', texto_unido)
    if placas: datos["placa"] = placas[0]
    
    # 2. Detectar Valor Económico (Busca el símbolo $ seguido de números)
    valores = re.findall(r'\$\s?[\d\.,]+', texto_unido)
    if valores: datos["valor"] = valores[0]
    
    # 3. Detectar Nombre (Busca secuencias largas de palabras en mayúsculas)
    # Se prioriza la detección de nombres que suelen estar después de "ASEGURADO" o "PROPIETARIO"
    for i, palabra in enumerate(texto_lista):
        if "NOMBRE" in palabra or "CLIENTE" in palabra or "ASEGURADO" in palabra:
            # Toma las siguientes 3 palabras como el nombre probable
            datos["nombre"] = " ".join(texto_lista[i+1:i+4])
            break

    # 4. Clasificar Siniestro
    if any(p in texto_unido for p in ["SINIESTRO", "CHOQUE", "RECLAMACION", "INDEMNIZACION"]):
        datos["siniestro"] = "SINIESTRO DETECTADO"
    
    return datos

# --- INTERFAZ DE USUARIO ---
st.sidebar.header("📋 Datos Organizados por IA")

# Inicializar sesión
if 'smart_data' not in st.session_state:
    st.session_state.smart_data = {"nombre": "", "placa": "", "valor": "", "siniestro": ""}

with st.sidebar.expander("👤 Información del Cliente", expanded=True):
    nombre_final = st.text_input("Nombre Extraído", value=st.session_state.smart_data.get("nombre", ""))
    
with st.sidebar.expander("🚗 Vehículo y Valor", expanded=True):
    placa_final = st.text_input("Placa", value=st.session_state.smart_data.get("placa", ""))
    valor_final = st.text_input("Valor Neto del Siniestro", value=st.session_state.smart_data.get("valor", ""))
    estado_final = st.selectbox("Estado", ["SINIESTRO DETECTADO", "SIN REGISTRO", "EN PROCESO"])

# --- CUERPO PRINCIPAL ---
st.markdown("<h2 style='text-align: center; color: #001e4d;'>🤖 Analizador de Documentos y Valores</h2>", unsafe_allow_html=True)

archivo = st.file_uploader("Sube la imagen del reporte", type=["jpg", "png", "jpeg"])

if archivo:
    with st.spinner("IA Analizando y Clasificando..."):
        img_pil = Image.open(archivo)
        img_np = np.array(img_pil)
        res_ocr = reader.readtext(img_np, detail=0)
        
        # Extraer datos estructurados
        extraidos = extraer_datos_inteligentes(res_ocr)
        st.session_state.smart_data = extraidos
        
        # Mostrar Previsualización
        st.success(f"✅ Se ha detectado información para: {extraidos['nombre']}")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(archivo, caption="Evidencia Original", use_container_width=True)
    with col2:
        st.info("📌 Desglose de Valores Detectados:")
        st.write(f"**Valor de Reclamación:** {extraidos['valor']}")
        st.write(f"**Estado:** {extraidos['siniestro']}")

    st.divider()

    if st.button("📥 GENERAR Y DESCARGAR PDF ESTRUCTURADO"):
        img_64 = base64.b64encode(archivo.getvalue()).decode()
        
        html_pdf = f"""
        <html>
        <head>
            <style>
                @page {{ size: A4; margin: 0; }}
                body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 0; }}
                .header {{ background: #001e4d; color: white; padding: 30px; text-align: center; }}
                .yellow-bar {{ background: #ffcc00; padding: 10px; text-align: center; font-weight: bold; font-size: 14px; }}
                .container {{ padding: 30px; }}
                .table-info {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .table-info td {{ padding: 15px; border: 1px solid #eee; }}
                .label {{ background: #f8f9fa; font-weight: bold; width: 30%; color: #666; font-size: 11px; }}
                .value {{ font-size: 14px; font-weight: bold; color: #333; }}
                .valor-destacado {{ color: #d32f2f; font-size: 18px; }}
                .img-box {{ text-align: center; margin-top: 20px; border: 1px solid #ddd; padding: 10px; }}
            </style>
        </head>
        <body>
            <div class="header"><h1>REPORTE DE VALIDACIÓN DE VALORES</h1></div>
            <div class="yellow-bar">DATOS EXTRAÍDOS POR SISTEMA IA</div>
            
            <div class="container">
                <table class="table-info">
                    <tr><td class="label">NOMBRE DEL CLIENTE</td><td class="value">{nombre_final}</td></tr>
                    <tr><td class="label">PLACA DEL VEHÍCULO</td><td class="value">{placa_final}</td></tr>
                    <tr><td class="label">ESTADO DE SINIESTRO</td><td class="value">{estado_final}</td></tr>
                    <tr><td class="label">VALOR DE RECLAMACIÓN</td><td class="value valor-destacado">{valor_final}</td></tr>
                </table>

                <div class="img-box">
                    <p style="font-size: 10px; color: #888;">EVIDENCIA ADJUNTA</p>
                    <img src="data:image/png;base64,{img_64}" style="max-width: 100%; max-height: 400px;">
                </div>
            </div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            HTML(string=html_pdf).write_pdf(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("📥 GUARDAR DOCUMENTO PDF", f, f"Validacion_{placa_final}.pdf", mime="application/pdf")
