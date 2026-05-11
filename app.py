import streamlit as st
from fpdf import FPDF
import tempfile
import re
import base64
import numpy as np
from PIL import Image, ImageOps
import easyocr

st.set_page_config(page_title="Validador CDA Técnico", layout="wide")

@st.cache_resource
def load_ocr():
    # Cargamos con soporte para números y letras claras
    return easyocr.Reader(['es'], gpu=False)

reader = load_ocr()

# --- BARRA LATERAL ---
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
            v = st.text_input(f"Monto {i+1}", value=item['valor'], key=f"recla_v_{i}")
        with col2:
            t = st.text_input(f"Tipo {i+1}", value=item['tipo'], key=f"recla_t_{i}")
        items_recla.append({"valor": v, "tipo": t})

# --- CUERPO PRINCIPAL ---
st.title("🚗 Analizador Técnico Automotriz")

col_info, col_img = st.columns([1.2, 1])

with col_info:
    st.subheader("🚥 Comparendos (SIMIT)")
    txt_simit = st.text_area("Pegar texto del SIMIT aquí:", height=150)
    
    multas_detectadas = []
    if txt_simit:
        montos = re.findall(r'\$\s?[\d\.,]{5,}', txt_simit)
        if montos:
            with st.expander("👁️ Ver Multas Extraídas", expanded=True):
                for m in list(set(montos)):
                    st.write(f"• {m}")
                    multas_detectadas.append(m)

with col_img:
    st.subheader("📸 Evidencia de Escaneo")
    archivo = st.file_uploader("Subir foto de RUNT / Fasecolda", type=["jpg", "png", "jpeg"])
    
    if archivo:
        if st.button("🔍 ESCANEAR IMAGEN"):
            with st.spinner("Procesando imagen con IA..."):
                # Abrir y optimizar imagen para OCR
                img_pil = Image.open(archivo).convert('RGB')
                # Aumentamos contraste para detectar mejor caracteres negros en fondo blanco
                img_gray = ImageOps.grayscale(img_pil)
                
                res = reader.readtext(np.array(img_pil), detail=0)
                txt_u = " ".join(res).upper().replace(" ", "") # Quitamos espacios para VIN
                
                # Regex agresiva para Placa
                p_match = re.search(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', txt_u)
                # Regex agresiva para VIN (17 caracteres)
                v_match = re.search(r'[A-HJ-NPR-Z0-9]{17}', txt_u)
                
                if p_match: st.session_state.v_data["placa"] = p_match.group()
                if v_match: st.session_state.v_data["vin"] = v_match.group()
                
                if not p_match and not v_match:
                    st.warning("No se detectó Placa/VIN automáticamente. Verifique la calidad de la imagen.")
                st.rerun()
        st.image(archivo, use_container_width=True)

# --- GENERAR PDF (SIN TOTALES) ---
if st.button("📥 GENERAR REPORTE DE SINIESTROS PDF"):
    if not archivo:
        st.error("Adjunte la imagen de evidencia.")
    else:
        pdf = FPDF()
        pdf.add_page()
        
        # Encabezado azul CDA
        pdf.set_fill_color(0, 30, 77); pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 15, "REPORTE TÉCNICO DE SINIESTROS Y HALLAZGOS", ln=True, align='C')
        
        # Datos Identificación
        pdf.set_text_color(0, 0, 0); pdf.ln(10)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(95, 9, f"PLACA: {placa_f}", border=1)
        pdf.cell(95, 9, f"VIN: {vin_f}", border=1, ln=True)
        pdf.cell(95, 9, f"VENCIMIENTO SOAT: {f_soat}", border=1)
        pdf.cell(95, 9, f"VENCIMIENTO TECNO: {f_tecno}", border=1, ln=True)
        
        # Sección Siniestros
        pdf.ln(8); pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 9, "DETALLE DE RECLAMACIONES / SINIESTROS", ln=True, fill=True, border=1)
        pdf.set_font("Arial", '', 10)
        for r in items_recla:
            pdf.cell(140, 8, f"Tipo: {r['tipo']}", border=1)
            pdf.cell(50, 8, r['valor'], border=1, ln=True)
        
        # Sección Multas (SIMIT)
        if multas_detectadas:
            pdf.ln(5); pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 9, "RESUMEN DE COMPARENDOS (SIMIT)", ln=True, fill=True, border=1)
            pdf.set_font("Arial", '', 10)
            for m in multas_detectadas:
                pdf.cell(140, 8, "Comparendo pendiente de pago", border=1)
                pdf.cell(50, 8, m, border=1, ln=True)
            
        # Imagen de Evidencia al final
        pdf.ln(10); pdf.set_font("Arial", 'B', 10); pdf.cell(190, 10, "EVIDENCIA FOTOGRÁFICA REGISTRADA", ln=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            Image.open(archivo).convert('RGB').save(tmp.name)
            pdf.image(tmp.name, x=10, w=180)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 DESCARGAR REPORTE FINAL", f, f"Reporte_{placa_f}.pdf")
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 DESCARGAR REPORTE FINAL", f, f"Validacion_{placa_f}.pdf")
