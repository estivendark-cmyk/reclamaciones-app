import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64
import easyocr
import numpy as np
from PIL import Image
import re

# Configuración inicial
st.set_page_config(page_title="Lector IA de Siniestros", layout="wide")

# Cargar el motor de lectura (OCR)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['es'])

reader = load_ocr()

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

# --- INTERFAZ ---
st.sidebar.header("📝 Datos Extraídos por IA")

# Inicializar estados si no existen
if 'txt_ia' not in st.session_state: st.session_state.txt_ia = ""
if 'siniestro_detectado' not in st.session_state: st.session_state.siniestro_detectado = "NO DETECTADO"

# Campos de transcripción (se llenarán con la IA)
with st.sidebar.expander("🚗 Información del Vehículo", expanded=True):
    placa = st.text_input("Placa Detectada", value="KCM702")
    marca = st.text_input("Marca/Línea", value="TOYOTA COROLLA CROSS")

with st.sidebar.expander("🚨 Estado del Siniestro (Auto)", expanded=True):
    # Esta variable se llenará sola al leer la imagen
    estado_ia = st.selectbox("Detección IA", ["SINIESTRO DETECTADO", "SIN REGISTRO", "EN PROCESO"], 
                             index=0 if st.session_state.siniestro_detectado == "SI" else 1)
    valor_recla = st.text_input("Valor de Reclamación", value="$ 5.467.111,00")

# --- CUERPO PRINCIPAL ---
st.markdown("<h2 style='color: #001e4d; text-align: center;'>🤖 Analizador Automático de Documentos</h2>", unsafe_allow_html=True)

archivo = st.file_uploader("Sube el pantallazo (RUNT/SIMIT/Aseguradora)", type=["jpg", "png", "jpeg"])

if archivo:
    # 1. PROCESAR IMAGEN CON IA
    with st.spinner("IA Analizando contenido..."):
        img_pil = Image.open(archivo)
        img_np = np.array(img_pil)
        resultados = reader.readtext(img_np, detail=0)
        texto_completo = " ".join(resultados).upper()
        st.session_state.txt_ia = texto_completo
        
        # Lógica de detección automática
        if any(palabra in texto_completo for palabra in ["SINIESTRO", "RECLAMACION", "CHOQUE", "INDEMNIZACION"]):
            st.session_state.siniestro_detectado = "SI"
            st.success("🚨 ¡Siniestro detectado automáticamente en el documento!")
        else:
            st.session_state.siniestro_detectado = "NO"

    # 2. MOSTRAR RESULTADOS
    col_img, col_txt = st.columns([1, 1])
    with col_img:
        st.image(archivo, caption="Evidencia", use_container_width=True)
    with col_txt:
        st.info("Texto extraído de la imagen (puedes copiar de aquí):")
        st.text_area("Lectura OCR", value=st.session_state.txt_ia, height=250)

    # 3. GENERACIÓN DE PDF (Columna de Siniestro incluida)
    st.divider()
    if st.button("✅ VALIDAR Y DESCARGAR PDF"):
        with st.spinner("Generando documento..."):
            img_base64 = base64.b64encode(archivo.getvalue()).decode()
            
            html_pdf = f"""
            <html>
            <head>
                <style>
                    @page {{ size: A4; margin: 0; }}
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
                    .header {{ background: #001e4d; color: white; padding: 30px; text-align: center; }}
                    .banner {{ background: #ffcc00; padding: 10px; text-align: center; font-weight: bold; }}
                    .container {{ padding: 20px; display: table; width: 100%; }}
                    .col {{ display: table-cell; width: 50%; padding: 10px; vertical-align: top; }}
                    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; }}
                    .siniestro-col {{ background: #fff5f5; border-left: 5px solid #d32f2f; }}
                    .label {{ font-weight: bold; color: #666; font-size: 10px; }}
                    .value {{ font-size: 14px; margin-bottom: 10px; }}
                    .detectado {{ color: #d32f2f; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header"><h1>REPORTE DE VALIDACIÓN AUTOMÁTICA</h1></div>
                <div class="banner">DOCUMENTO INFORMATIVO GENERADO POR IA</div>
                
                <div class="container">
                    <div class="col">
                        <div class="card">
                            <div class="label">PLACA VEHÍCULO</div><div class="value">{placa}</div>
                            <div class="label">MARCA/LÍNEA</div><div class="value">{marca}</div>
                        </div>
                        <div class="card siniestro-col">
                            <div class="label">DETECCIÓN AUTOMÁTICA DE SINIESTRO</div>
                            <div class="value detectado">{estado_ia}</div>
                            <div class="label">VALOR REGISTRADO</div>
                            <div class="value">{valor_recla}</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="card">
                            <div class="label">EVIDENCIA ESCANEADA</div>
                            <img src="data:image/png;base64,{img_base64}" style="width:100%; border:1px solid #eee;">
                        </div>
                    </div>
                </div>
                <div style="padding:20px;">
                    <div class="card">
                        <div class="label">TRANSCRIPCIÓN COMPLETA DE LA IMAGEN</div>
                        <div style="font-size: 9px; color: #444;">{st.session_state.txt_ia[:1000]}...</div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                HTML(string=html_pdf).write_pdf(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 DESCARGAR REPORTE AHORA", f, f"Reporte_{placa}.pdf", mime="application/pdf")
            os.unlink(tmp.name)
