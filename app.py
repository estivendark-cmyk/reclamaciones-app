import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64
import easyocr
import numpy as np
from PIL import Image
import re

# Configuración
st.set_page_config(page_title="Analizador de Historial de Siniestros", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['es'])

reader = load_ocr()

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

# --- LÓGICA DE EXTRACCIÓN MÚLTIPLE ---
def extraer_multiples_siniestros(texto_lista):
    texto_unido = " ".join(texto_lista).upper()
    
    # 1. Buscar todos los montos de dinero detectados
    # Busca patrones como $ 1.000.000 o $500,000
    montos_detectados = re.findall(r'\$\s?[\d\.,]{4,}', texto_unido)
    
    # 2. Buscar placa
    placas = re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', texto_unido)
    placa = placas[0] if placas else "KCM702"
    
    # 3. Intentar extraer nombre
    nombre = "NO DETECTADO"
    for i, p in enumerate(texto_lista):
        if any(x in p.upper() for x in ["NOMBRE", "ASEGURADO", "PROPIETARIO"]):
            nombre = " ".join(texto_lista[i+1:i+4])
            break
            
    return nombre, placa, list(set(montos_detectados)) # Eliminamos duplicados

# --- INTERFAZ ---
st.sidebar.header("📋 Desglose de Historial")

if 'lista_siniestros' not in st.session_state:
    st.session_state.lista_siniestros = []

with st.sidebar.expander("👤 Datos Generales", expanded=True):
    nombre_f = st.text_input("Nombre Asegurado", value=st.session_state.get('nombre_ia', ""))
    placa_f = st.text_input("Placa", value=st.session_state.get('placa_ia', ""))

with st.sidebar.expander("💰 Lista de Reclamaciones Detectadas", expanded=True):
    # Aquí permitimos editar los valores que la IA encontró
    siniestros_editados = []
    for i, monto in enumerate(st.session_state.lista_siniestros):
        val = st.text_input(f"Siniestro #{i+1}", value=monto, key=f"sin_{i}")
        desc = st.text_input(f"Detalle #{i+1}", value="Reclamación registrada", key=f"det_{i}")
        siniestros_editados.append({"monto": val, "detalle": desc})

# --- CUERPO PRINCIPAL ---
st.markdown("<h2 style='text-align: center;'>🕵️ Analizador de Historial Múltiple</h2>", unsafe_allow_html=True)

archivo = st.file_uploader("Subir imagen con múltiples reclamaciones", type=["jpg", "png", "jpeg"])

if archivo:
    if st.button("🔍 ANALIZAR IMAGEN Y DESGLOSAR"):
        with st.spinner("IA Identificando todos los montos..."):
            img = Image.open(archivo)
            res = reader.readtext(np.array(img), detail=0)
            nombre, placa, montos = extraer_multiples_siniestros(res)
            
            st.session_state.nombre_ia = nombre
            st.session_state.placa_ia = placa
            st.session_state.lista_siniestros = montos
            st.rerun()

    if st.session_state.lista_siniestros:
        st.success(f"Se han detectado {len(st.session_state.lista_siniestros)} montos diferentes.")
        
        # Generar PDF
        if st.button("📥 GENERAR REPORTE DE HISTORIAL COMPLETO"):
            img_64 = base64.b64encode(archivo.getvalue()).decode()
            
            # Construir filas de la tabla dinámicamente
            filas_tabla = ""
            for s in siniestros_editados:
                filas_tabla += f"""
                <tr>
                    <td style="padding:10px; border:1px solid #eee;">{s['detalle']}</td>
                    <td style="padding:10px; border:1px solid #eee; font-weight:bold; color:red;">{s['monto']}</td>
                </tr>
                """

            html_pdf = f"""
            <html>
            <head>
                <style>
                    @page {{ size: A4; margin: 0; }}
                    body {{ font-family: Arial; margin: 0; padding: 0; }}
                    .header {{ background: #001e4d; color: white; padding: 25px; text-align: center; }}
                    .container {{ padding: 30px; }}
                    .info-box {{ margin-bottom: 20px; background: #f8f9fa; padding: 15px; border-radius: 5px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    th {{ background: #eee; text-align: left; padding: 10px; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header"><h1>HISTORIAL INTEGRAL DE RECLAMACIONES</h1></div>
                <div class="container">
                    <div class="info-box">
                        <b>ASEGURADO:</b> {nombre_f}<br>
                        <b>PLACA:</b> {placa_f}
                    </div>
                    
                    <h3>DESGLOSE DE SINIESTROS ENCONTRADOS</h3>
                    <table>
                        <thead><tr><th>DESCRIPCIÓN / DETALLE</th><th>VALOR RECLAMADO</th></tr></thead>
                        <tbody>{filas_tabla}</tbody>
                    </table>

                    <div style="margin-top:20px; text-align:center;">
                        <p style="font-size:10px; color:#666;">EVIDENCIA FOTOGRÁFICA</p>
                        <img src="data:image/png;base64,{img_64}" style="max-width:80%; border:1px solid #ddd;">
                    </div>
                </div>
            </body>
            </html>
            """
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                HTML(string=html_pdf).write_pdf(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 DESCARGAR REPORTE MULTI-SINIESTRO", f, f"Historial_{placa_f}.pdf")
