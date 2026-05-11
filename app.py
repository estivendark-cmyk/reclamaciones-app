import streamlit as st
from fpdf import FPDF
import tempfile
import re
import base64
import numpy as np
from PIL import Image
import easyocr

st.set_page_config(page_title="Validador Técnico Automotriz", layout="wide")

# Cargamos el motor de IA (Solo una vez)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['es'], gpu=False)

reader = load_ocr()

def limpiar_monto(texto):
    numeros = re.sub(r'[^\d]', '', texto)
    return int(numeros) if numeros else 0

# --- LÓGICA DE DETECCIÓN ---
def detectar_vehiculo(texto_lista):
    texto_unido = " ".join(texto_lista).upper()
    
    # Buscar Placa (Formatos colombianos comunes)
    placa = next(iter(re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', texto_unido)), "")
    
    # Buscar VIN (17 caracteres alfanuméricos, omitiendo I, O, Q)
    vin = next(iter(re.findall(r'[A-HJ-NPR-Z0-9]{17}', texto_unido)), "")
    
    # Buscar Montos de dinero
    montos = re.findall(r'\$\s?[\d\.,]{5,}', texto_unido)
    
    return placa, vin, list(set(montos))

# --- BARRA LATERAL ---
st.sidebar.header("📋 Información del Vehículo")

if 'vehiculo' not in st.session_state:
    st.session_state.vehiculo = {"placa": "", "vin": "", "siniestros": []}

with st.sidebar.expander("🚗 Datos de Identificación", expanded=True):
    placa_f = st.text_input("Placa", value=st.session_state.vehiculo["placa"])
    vin_f = st.text_input("Número VIN (Chasis)", value=st.session_state.vehiculo["vin"])

with st.sidebar.expander("💰 Reclamaciones", expanded=True):
    if st.button("➕ Agregar Fila"):
        st.session_state.vehiculo["siniestros"].append({"valor": "$ 0", "tipo": "Reclamación"})
    
    reclamaciones_finales = []
    suma_total = 0
    for i, item in enumerate(st.session_state.vehiculo["siniestros"]):
        v = st.text_input(f"Valor {i+1}", value=item.get('valor', '$ 0'), key=f"v_{i}")
        t = st.text_input(f"Tipo {i+1}", value=item.get('tipo', 'Reclamación'), key=f"t_{i}")
        suma_total += limpiar_monto(v)
        reclamaciones_finales.append({"valor": v, "tipo": t})
    
    st.divider()
    st.metric("SUMA TOTAL VALIDADA", f"$ {suma_total:,.0f}")

# --- CUERPO PRINCIPAL ---
st.title("🕵️ Validador Técnico de Siniestralidad")

# Links Públicos
c1, c2, c3 = st.columns(3)
with c1: st.link_button("🌐 RUNT", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo")
with c2: st.link_button("🚦 SIMIT", "https://www.fcm.org.co/simit/#/estado-cuenta")
with c3: st.link_button("📊 FASECOLDA", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx")

st.divider()

col_ev, col_img = st.columns(2)

with col_ev:
    st.subheader("📄 Transcripciones de Soporte")
    txt_soat = st.text_area("SOAT / Tecno / Otros:", height=150, placeholder="Pega aquí el texto para el PDF...")
    
with col_img:
    st.subheader("📸 Evidencia Fotográfica")
    archivo = st.file_uploader("Subir imagen (RUNT/Fasecolda)", type=["jpg", "png", "jpeg"])
    
    if archivo:
        if st.button("🚀 ESCANEAR PLACA Y VIN"):
            with st.spinner("IA analizando imagen..."):
                img = Image.open(archivo).convert('RGB')
                res = reader.readtext(np.array(img), detail=0)
                p, v, m = detectar_vehiculo(res)
                
                # Actualizar estado
                st.session_state.vehiculo["placa"] = p if p else placa_f
                st.session_state.vehiculo["vin"] = v if v else vin_f
                if m:
                    for val in m:
                        st.session_state.vehiculo["siniestros"].append({"valor": val, "tipo": "Detectado"})
                st.rerun()
        st.image(archivo, width=350)

# --- GENERACIÓN DE PDF ---
if st.button("📥 DESCARGAR REPORTE FINAL PDF"):
    if not archivo:
        st.error("Sube la imagen de evidencia")
    else:
        pdf = FPDF()
        pdf.add_page()
        # Encabezado
        pdf.set_fill_color(0, 30, 77)
        pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 20, "INFORME TÉCNICO AUTOMOTRIZ", ln=True, align='C')
        
        # Datos del vehículo
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 12)
        pdf.ln(15)
        pdf.cell(95, 10, f"PLACA: {placa_f}", border=1)
        pdf.cell(95, 10, f"VIN: {vin_f}", border=1, ln=True)
        
        # Tabla de siniestros
        pdf.ln(10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(100, 10, "DESCRIPCIÓN", border=1, fill=True)
        pdf.cell(90, 10, "VALOR", border=1, fill=True, ln=True)
        
        pdf.set_font("Arial", '', 11)
        for item in reclamaciones_finales:
            pdf.cell(100, 10, item['tipo'], border=1)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(90, 10, item['valor'], border=1, ln=True)
            pdf.set_text_color(0, 0, 0)
            
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(100, 10, "SUMA TOTAL VALIDADA", border=1, fill=True)
        pdf.cell(90, 10, f"$ {suma_total:,.0f}", border=1, ln=True, fill=True)
        
        # Transcripciones
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 10, "TRANSCRIPCIONES DE SOPORTE", ln=True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(190, 5, txt_soat)

        # Imagen
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            img_ev = Image.open(archivo).convert('RGB')
            img_ev.save(tmp.name)
            pdf.ln(10)
            pdf.image(tmp.name, x=10, w=180)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 DESCARGAR PDF", f, f"Reporte_{placa_f}.pdf")
