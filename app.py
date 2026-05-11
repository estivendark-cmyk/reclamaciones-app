import streamlit as st
from fpdf import FPDF
import tempfile
import re
import base64
import numpy as np
from PIL import Image
import easyocr

st.set_page_config(page_title="Scanner CDA Pro", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['es'], gpu=False)

reader = load_ocr()

def limpiar_monto(texto):
    numeros = re.sub(r'[^\d]', '', texto)
    return int(numeros) if numeros else 0

# --- MOTOR DE ESCANEO ---
def escanear_documento(texto_lista):
    texto_unido = " ".join(texto_lista).upper()
    
    # Identificación
    placa = next(iter(re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', texto_unido)), "")
    vin = next(iter(re.findall(r'[A-HJ-NPR-Z0-9]{17}', texto_unido)), "")
    
    # Montos por categorías
    datos_detectados = {"soat": "", "tecno": "", "comparendos": [], "reclamaciones": []}
    
    for i, bloque in enumerate(texto_lista):
        b = bloque.upper()
        # Buscar montos de dinero
        if "$" in b or any(term in b for term in ["VALOR", "SALDO", "TOTAL"]):
            monto = next(iter(re.findall(r'\$\s?[\d\.,]{5,}', b)), b)
            
            # Clasificar por contexto cercano
            contexto = " ".join(texto_lista[max(0, i-2):i+3]).upper()
            if "SOAT" in contexto: datos_detectados["soat"] = monto
            elif "TECNOMEC" in contexto or "RTM" in contexto: datos_detectados["tecno"] = monto
            elif "COMPARENDO" in contexto or "MULTA" in contexto: datos_detectados["comparendos"].append(monto)
            else: datos_detectados["reclamaciones"].append(monto)
            
    return placa, vin, datos_detectados

# --- MENÚ IZQUIERDO (SIDEBAR) ---
if 'v_data' not in st.session_state:
    st.session_state.v_data = {"placa": "", "vin": "", "soat": "", "tecno": "", "multas": [], "recla": []}

st.sidebar.header("📋 Datos del Vehículo")

with st.sidebar:
    placa_f = st.text_input("📍 Placa", value=st.session_state.v_data["placa"])
    vin_f = st.text_input("🆔 VIN / Chasis", value=st.session_state.v_data["vin"])
    
    st.divider()
    st.subheader("💰 Gastos y Reclamaciones")
    val_soat = st.text_input("📝 Valor SOAT", value=st.session_state.v_data["soat"])
    val_tecno = st.text_input("🛠️ Valor Tecnomecánica", value=st.session_state.v_data["tecno"])
    
    # Listas dinámicas para Multas y Reclamaciones
    st.markdown("**🚥 Comparendos / Multas**")
    for i, m in enumerate(st.session_state.v_data["multas"]):
        st.session_state.v_data["multas"][i] = st.text_input(f"Multa {i+1}", value=m, key=f"m_{i}")
        
    st.markdown("**🛡️ Otras Reclamaciones (PPD/PPP)**")
    for i, r in enumerate(st.session_state.v_data["recla"]):
        st.session_state.v_data["recla"][i] = st.text_input(f"Recla {i+1}", value=r, key=f"r_{i}")

    # Cálculo de Suma Total
    total = limpiar_monto(val_soat) + limpiar_monto(val_tecno)
    total += sum(limpiar_monto(x) for x in st.session_state.v_data["multas"])
    total += sum(limpiar_monto(x) for x in st.session_state.v_data["recla"])
    
    st.divider()
    st.metric("TOTAL GENERAL", f"$ {total:,.0f}")

# --- CUERPO PRINCIPAL ---
st.title("🚀 Scanner CDA - Validador Automotriz")

col_input, col_links = st.columns([2, 1])

with col_links:
    st.info("🔗 Enlaces de Consulta")
    st.link_button("🌐 Ir a RUNT", "https://www.runt.com.co/", use_container_width=True)
    st.link_button("🚦 Ir a SIMIT", "https://www.fcm.org.co/simit/", use_container_width=True)
    st.link_button("📊 FASECOLDA", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx", use_container_width=True)

with col_input:
    archivo = st.file_uploader("📸 Sube evidencia (Imagen)", type=["jpg", "png", "jpeg"])
    if archivo:
        if st.button("🔍 ESCANEAR E IMPORTAR AL MENÚ"):
            with st.spinner("IA extrayendo datos..."):
                img = Image.open(archivo).convert('RGB')
                res = reader.readtext(np.array(img), detail=0)
                p, v, d = escanear_documento(res)
                
                # Cargar al menú izquierdo
                st.session_state.v_data["placa"] = p if p else placa_f
                st.session_state.v_data["vin"] = v if v else vin_f
                st.session_state.v_data["soat"] = d["soat"] if d["soat"] else val_soat
                st.session_state.v_data["tecno"] = d["tecno"] if d["tecno"] else val_tecno
                st.session_state.v_data["multas"].extend(d["comparendos"])
                st.session_state.v_data["recla"].extend(d["reclamaciones"])
                st.rerun()
        st.image(archivo, width=400)

# --- GENERAR PDF ---
if st.button("📥 GENERAR INFORME FINAL PDF"):
    if not archivo:
        st.error("Adjunta una imagen para el reporte")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.set_fill_color(0, 30, 77); pdf.set_text_color(255, 255, 255)
        pdf.cell(190, 15, "REPORTE TÉCNICO DE INSPECCIÓN", ln=True, align='C', fill=True)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12); pdf.ln(10)
        pdf.cell(95, 10, f"PLACA: {placa_f}", border=1)
        pdf.cell(95, 10, f"VIN: {vin_f}", border=1, ln=True)
        
        pdf.ln(5); pdf.cell(190, 10, "DETALLE FINANCIERO", ln=True, fill=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(140, 8, "VALOR SOAT", border=1); pdf.cell(50, 8, val_soat, border=1, ln=True)
        pdf.cell(140, 8, "VALOR TECNOMECÁNICA", border=1); pdf.cell(50, 8, val_tecno, border=1, ln=True)
        
        for m in st.session_state.v_data["multas"]:
            pdf.cell(140, 8, "COMPARENDO / MULTA", border=1); pdf.cell(50, 8, m, border=1, ln=True)
        for r in st.session_state.v_data["recla"]:
            pdf.cell(140, 8, "RECLAMACIÓN / OTROS", border=1); pdf.cell(50, 8, r, border=1, ln=True)
            
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(140, 10, "TOTAL GENERAL VALIDADO", border=1, fill=True)
        pdf.cell(50, 10, f"$ {total:,.0f}", border=1, ln=True, fill=True)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            Image.open(archivo).convert('RGB').save(tmp.name)
            pdf.ln(10); pdf.image(tmp.name, x=10, w=180)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 DESCARGAR RESULTADOS", f, f"Inspeccion_{placa_f}.pdf")
