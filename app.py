import streamlit as st
from fpdf import FPDF
import tempfile
import re
import base64
import numpy as np
from PIL import Image, ImageOps
import easyocr

st.set_page_config(page_title="Validador Técnico CDA", layout="wide")

@st.cache_resource
def load_ocr():
    # Motor de IA optimizado para lectura de caracteres técnicos
    return easyocr.Reader(['es'], gpu=False)

reader = load_ocr()

# --- BARRA LATERAL (GESTIÓN DE DATOS) ---
st.sidebar.header("📋 Identificación Vehicular")

if 'v_data' not in st.session_state:
    st.session_state.v_data = {"placa": "", "vin": "", "recla": []}

with st.sidebar:
    placa_f = st.text_input("📍 Placa Detectada", value=st.session_state.v_data["placa"])
    vin_f = st.text_input("🆔 VIN / Chasis", value=st.session_state.v_data["vin"])
    
    st.divider()
    st.subheader("🗓️ Fechas Técnicas")
    f_soat = st.date_input("Vencimiento SOAT")
    f_tecno = st.date_input("Vencimiento Tecnomecánica")
    
    st.divider()
    st.subheader("🛡️ Reporte de Siniestros")
    if st.button("➕ Añadir Hallazgo"):
        st.session_state.v_data["recla"].append({"valor": "$ 0", "tipo": "PPD"})
    
    items_recla = []
    for i, item in enumerate(st.session_state.v_data["recla"]):
        col1, col2 = st.columns(2)
        with col1:
            v = st.text_input(f"Monto {i+1}", value=item['valor'], key=f_recla_v_{i})
        with col2:
            t = st.text_input(f"Tipo {i+1}", value=item['tipo'], key=f_recla_t_{i})
        items_recla.append({"valor": v, "tipo": t})

# --- CUERPO PRINCIPAL ---
st.title("🚗 Analizador Técnico de Historial")

# --- SECCIÓN DE LINKS (REINCORPORADA) ---
st.info("🔗 Accesos Rápidos a Consultas Oficiales")
c1, c2, c3 = st.columns(3)
with c1: st.link_button("🌐 CONSULTA RUNT", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo", use_container_width=True)
with c2: st.link_button("🚦 ESTADO SIMIT", "https://www.fcm.org.co/simit/#/estado-cuenta", use_container_width=True)
with c3: st.link_button("📊 FASECOLDA", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx", use_container_width=True)

st.divider()

col_info, col_img = st.columns([1.2, 1])

with col_info:
    st.subheader("🚥 Historial SIMIT (Comparendos)")
    txt_simit = st.text_area("Pega aquí el texto de la consulta del SIMIT:", height=150, placeholder="Copia y pega el detalle de multas aquí...")
    
    multas_detectadas = []
    if txt_simit:
        # Extraer montos de dinero del texto pegado
        montos = re.findall(r'\$\s?[\d\.,]{5,}', txt_simit)
        if montos:
            with st.expander("👁️ Ver Multas Extraídas del Texto", expanded=True):
                for m in list(set(montos)):
                    st.write(f"• {m}")
                    multas_detectadas.append(m)

with col_img:
    st.subheader("📸 Escaneo de Evidencia")
    archivo = st.file_uploader("Subir foto de RUNT / Fasecolda / Chasis", type=["jpg", "png", "jpeg"])
    
    if archivo:
        if st.button("🔍 INICIAR ESCANEO DE IA"):
            with st.spinner("Analizando imagen..."):
                img_pil = Image.open(archivo).convert('RGB')
                # OCR sobre la imagen original
                res = reader.readtext(np.array(img_pil), detail=0)
                txt_completo = "".join(res).upper().replace(" ", "").replace("-", "")
                
                # Búsqueda de Placa (AAA111 o AAA11A)
                p_match = re.search(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', txt_completo)
                # Búsqueda de VIN (17 caracteres estándar ISO)
                v_match = re.search(r'[A-HJ-NPR-Z0-9]{17}', txt_completo)
                
                if p_match: st.session_state.v_data["placa"] = p_match.group()
                if v_match: st.session_state.v_data["vin"] = v_match.group()
                
                if not p_match and not v_match:
                    st.warning("No se detectaron datos. Intente con una foto más cercana o con mejor luz.")
                st.rerun()
        st.image(archivo, use_container_width=True)

# --- GENERAR PDF ---
st.divider()
if st.button("📥 GENERAR REPORTE DE SINIESTROS PDF"):
    if not archivo:
        st.error("Es obligatorio subir una imagen de evidencia.")
    else:
        pdf = FPDF()
        pdf.add_page()
        
        # Encabezado Estilo CDA
        pdf.set_fill_color(0, 30, 77)
        pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 15, "REPORTE TÉCNICO DE SINIESTROS Y HALLAZGOS", ln=True, align='C')
        
        # Información del Vehículo
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(95, 9, f"PLACA: {placa_f}", border=1)
        pdf.cell(95, 9, f"VIN: {vin_f}", border=1, ln=True)
        pdf.cell(95, 9, f"VENCIMIENTO SOAT: {f_soat}", border=1)
        pdf.cell(95, 9, f"VENCIMIENTO TECNO: {f_tecno}", border=1, ln=True)
        
        # Detalle Siniestros
        pdf.ln(8)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 9, "DETALLE DE RECLAMACIONES / SINIESTROS", ln=True, fill=True, border=1)
        pdf.set_font("Arial", '', 10)
        for r in items_recla:
            pdf.cell(140, 8, f"Tipo: {r['tipo']}", border=1)
            pdf.cell(50, 8, r['valor'], border=1, ln=True)
        
        # Detalle Multas
        if multas_detectadas:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 9, "RESUMEN DE COMPARENDOS (SIMIT)", ln=True, fill=True, border=1)
            pdf.set_font("Arial", '', 10)
            for m in multas_detectadas:
                pdf.cell(140, 8, "Comparendo / Multa detectada", border=1)
                pdf.cell(50, 8, m, border=1, ln=True)
            
        # Imagen de Evidencia
        pdf.ln(10)
        pdf.set_font("
