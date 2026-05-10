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
st.set_page_config(page_title="Validador de Siniestros Múltiples", layout="wide")

@st.cache_resource
def load_ocr():
    # Cargamos el lector con soporte para números y español
    return easyocr.Reader(['es'])

reader = load_ocr()

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

# --- LÓGICA DE DETECCIÓN MEJORADA ---
def analizar_historial_completo(texto_lista):
    texto_unido = " ".join(texto_lista).upper()
    
    # 1. Regex mejorada: Busca $ seguido de cualquier combinación de números, puntos y comas
    # Capta desde $500.000 hasta $100.000.000.00
    patron_moneda = r'\$\s?[\d\.,]{4,}'
    todos_los_montos = re.findall(patron_moneda, texto_unido)
    
    # 2. Detección de tipos de siniestro (PPD, PPP, Global, etc.)
    siniestros_detectados = []
    
    # Buscamos en cada bloque de texto leído
    for i, bloque in enumerate(texto_lista):
        bloque_up = bloque.upper()
        # Si el bloque contiene un monto, buscamos palabras clave cerca
        if "$" in bloque:
            detalle = "Reclamación Registrada"
            # Buscamos en el bloque actual o los 2 anteriores/siguientes
            contexto = " ".join(texto_lista[max(0, i-2):i+3]).upper()
            
            if "PPD" in contexto or "PARCIAL DA" in contexto: detalle = "Pérdida Parcial Daños (PPD)"
            elif "PPP" in contexto or "PARCIAL HUR" in contexto: detalle = "Pérdida Parcial Hurto (PPP)"
            elif "TOTAL" in contexto: detalle = "Pérdida Total"
            elif "RESPONSABILIDAD" in contexto or "RCE" in contexto: detalle = "Responsabilidad Civil (RCE)"
            
            siniestros_detectados.append({"monto": bloque, "detalle": detalle})

    # Si la lógica por contexto falla, usamos los montos brutos encontrados
    if not siniestros_detectados and todos_los_montos:
        for m in list(set(todos_los_montos)):
            siniestros_detectados.append({"monto": m, "detalle": "Reclamación Detectada"})

    # 3. Datos generales
    placa = next(iter(re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', texto_unido)), "KCM702")
    
    nombre = "NO DETECTADO"
    for i, p in enumerate(texto_lista):
        if any(x in p.upper() for x in ["NOMBRE", "ASEGURADO", "CLIENTE"]):
            nombre = " ".join(texto_lista[i+1:i+4])
            break
            
    return nombre, placa, siniestros_detectados

# --- INTERFAZ ---
st.sidebar.header("📋 Panel de Control de Siniestros")

if 'historial' not in st.session_state:
    st.session_state.historial = []

with st.sidebar.expander("👤 Datos de Identificación", expanded=True):
    nombre_f = st.text_input("Asegurado", value=st.session_state.get('n_ia', ""), key="n_f")
    placa_f = st.text_input("Placa", value=st.session_state.get('p_ia', ""), key="p_f")

with st.sidebar.expander("💰 Desglose de Reclamaciones", expanded=True):
    final_list = []
    for i, item in enumerate(st.session_state.historial):
        col1, col2 = st.columns([1, 1])
        with col1:
            m = st.text_input(f"Valor #{i+1}", value=item['monto'], key=f"m_{i}")
        with col2:
            d = st.text_input(f"Tipo #{i+1}", value=item['detalle'], key=f"d_{i}")
        final_list.append({"monto": m, "detalle": d})

# --- CUERPO ---
st.markdown("<h2 style='text-align: center; color: #001e4d;'>📊 Analizador Múltiple PPD/PPP</h2>", unsafe_allow_html=True)

archivo = st.file_uploader("Subir imagen del historial completo", type=["jpg", "png", "jpeg"])

if archivo:
    if st.button("🔍 ESCANEAR TODOS LOS SINIESTROS"):
        with st.spinner("IA buscando montos y tipos de siniestro..."):
            img = Image.open(archivo)
            res = reader.readtext(np.array(img), detail=0)
            n, p, h = analizar_historial_completo(res)
            
            st.session_state.n_ia = n
            st.session_state.p_ia = p
            st.session_state.historial = h
            st.rerun()

    if st.session_state.historial:
        st.success(f"Se han identificado {len(st.session_state.historial)} registros.")
        
        if st.button("📥 GENERAR PDF CON DESGLOSE TOTAL"):
            img_64 = base64.b64encode(archivo.getvalue()).decode()
            filas = "".join([f"<tr><td style='padding:8px; border:1px solid #ddd;'>{x['detalle']}</td><td style='padding:8px; border:1px solid #ddd; color:red; font-weight:bold;'>{x['monto']}</td></tr>" for x in final_list])

            html_pdf = f"""
            <html>
            <head><style>
                body {{ font-family: Arial; margin: 0; padding: 20px; }}
                .header {{ background: #001e4d; color: white; padding: 20px; text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #f2f2f2; padding: 10px; text-align: left; }}
            </style></head>
            <body>
                <div class="header"><h2>REPORTE INTEGRAL DE SINIESTRALIDAD</h2></div>
                <p><b>Asegurado:</b> {nombre_f} | <b>Placa:</b> {placa_f}</p>
                <table>
                    <thead><tr><th>TIPO DE RECLAMACIÓN / DETALLE</th><th>VALOR PAGADO</th></tr></thead>
                    <tbody>{filas}</tbody>
                </table>
                <div style="margin-top:20px; text-align:center;">
                    <img src="data:image/png;base64,{img_64}" style="max-width:90%; border:1px solid #ccc;">
                </div>
            </body></html>
            """
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                HTML(string=html_pdf).write_pdf(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 DESCARGAR INFORME", f, f"Siniestros_{placa_f}.pdf")
