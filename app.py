import streamlit as st
from fpdf import FPDF
import tempfile
import re
import base64
import numpy as np
from PIL import Image
import easyocr

st.set_page_config(page_title="Validador CDA & Siniestros", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['es'], gpu=False)

reader = load_ocr()

def limpiar_monto(texto):
    numeros = re.sub(r'[^\d]', '', texto)
    return int(numeros) if numeros else 0

# --- BARRA LATERAL (DATOS DEL VEHÍCULO) ---
st.sidebar.header("📋 Información Técnica")

if 'v_data' not in st.session_state:
    st.session_state.v_data = {"placa": "", "vin": "", "recla": []}

with st.sidebar:
    placa_f = st.text_input("📍 Placa", value=st.session_state.v_data["placa"])
    vin_f = st.text_input("🆔 VIN / Chasis", value=st.session_state.v_data["vin"])
    
    st.divider()
    st.subheader("🗓️ Vencimientos")
    f_soat = st.date_input("Fecha Vencimiento SOAT")
    f_tecno = st.date_input("Fecha Vencimiento Tecno")
    
    st.divider()
    st.subheader("🛡️ Historial de Siniestros")
    if st.button("➕ Agregar Reclamación"):
        st.session_state.v_data["recla"].append({"valor": "$ 0", "tipo": "PPD"})
    
    items_recla = []
    suma_recla = 0
    for i, item in enumerate(st.session_state.v_data["recla"]):
        v = st.text_input(f"Valor #{i+1}", value=item['valor'], key=f"recla_v_{i}")
        t = st.text_input(f"Tipo #{i+1}", value=item['tipo'], key=f"recla_t_{i}")
        suma_recla += limpiar_monto(v)
        items_recla.append({"valor": v, "tipo": t})

# --- CUERPO PRINCIPAL ---
st.title("🚗 Validador de Historial Automotriz")

col_info, col_img = st.columns([1.5, 1])

with col_info:
    st.subheader("🚥 Comparendos y Multas (SIMIT)")
    txt_simit = st.text_area("Pega aquí el texto copiado del SIMIT:", height=150, 
                             placeholder="Pega el historial de comparendos aquí...")
    
    multas_detectadas = []
    if txt_simit:
        # Extraer montos de dinero del texto pegado
        montos_simit = re.findall(r'\$\s?[\d\.,]{5,}', txt_simit)
        if montos_simit:
            with st.expander("✅ Multas detectadas (Haz clic para ver)", expanded=True):
                for m in list(set(montos_simit)):
                    st.write(f"🚩 Comparendo detectado por valor de: **{m}**")
                    multas_detectadas.append(m)
    
    suma_multas = sum(limpiar_monto(x) for x in multas_detectadas)
    st.metric("Total en Multas", f"$ {suma_multas:,.0f}")

with col_img:
    st.subheader("📸 Evidencia RUNT / Fasecolda")
    archivo = st.file_uploader("Subir imagen de soporte", type=["jpg", "png", "jpeg"])
    if archivo:
        if st.button("🔍 Escanear Placa y VIN"):
            with st.spinner("Buscando datos en la imagen..."):
                img = Image.open(archivo).convert('RGB')
                res = reader.readtext(np.array(img), detail=0)
                txt_u = " ".join(res).upper()
                p = next(iter(re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', txt_u)), "")
                v = next(iter(re.findall(r'[A-HJ-NPR-Z0-9]{17}', txt_u)), "")
                st.session_state.v_data["placa"] = p if p else placa_f
                st.session_state.v_data["vin"] = v if v else vin_f
                st.rerun()
        st.image(archivo, use_container_width=True)

# --- SUMA TOTAL Y PDF ---
st.divider()
total_general = suma_recla + suma_multas
st.markdown(f"### 💰 IMPACTO ECONÓMICO TOTAL: **$ {total_general:,.0f}**")

if st.button("📥 GENERAR INFORME TÉCNICO PDF"):
    if not archivo:
        st.error("Por favor sube la evidencia fotográfica.")
    else:
        pdf = FPDF()
        pdf.add_page()
        
        # Encabezado
        pdf.set_fill_color(0, 30, 77); pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 20, "REPORTE TÉCNICO DE VALIDACIÓN", ln=True, align='C')
        
        # Datos Principales
        pdf.set_text_color(0, 0, 0); pdf.ln(15)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(95, 10, f"PLACA: {placa_f}", border=1)
        pdf.cell(95, 10, f"VIN: {vin_f}", border=1, ln=True)
        pdf.cell(95, 10, f"VENCE SOAT: {f_soat}", border=1)
        pdf.cell(95, 10, f"VENCE TECNO: {f_tecno}", border=1, ln=True)
        
        # Tabla Siniestros
        pdf.ln(10); pdf.set_fill_color(230, 230, 230)
        pdf.cell(190, 10, "DETALLE DE SINIESTROS / RECLAMACIONES", ln=True, fill=True)
        pdf.set_font("Arial", '', 10)
        for r in items_recla:
            pdf.cell(140, 8, r['tipo'], border=1)
            pdf.cell(50, 8, r['valor'], border=1, ln=True)
        
        # Tabla Multas
        pdf.ln(5); pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "COMPARENDOS DETECTADOS (SIMIT)", ln=True, fill=True)
        pdf.set_font("Arial", '', 10)
        for m in multas_detectadas:
            pdf.cell(140, 8, "MULTA PENDIENTE", border=1)
            pdf.cell(50, 8, m, border=1, ln=True)
            
        # Total
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(140, 12, "VALOR TOTAL ESTIMADO", border=1, fill=True)
        pdf.cell(50, 12, f"$ {total_general:,.0f}", border=1, ln=True, fill=True)
        
        # Imagen
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            Image.open(archivo).convert('RGB').save(tmp.name)
            pdf.ln(10); pdf.image(tmp.name, x=10, w=180)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 DESCARGAR REPORTE FINAL", f, f"Validacion_{placa_f}.pdf")
