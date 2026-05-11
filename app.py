import streamlit as st
from fpdf import FPDF
import tempfile
import re
import numpy as np
from PIL import Image
import easyocr
import os

st.set_page_config(page_title="Validador Técnico CDA Colombia", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['es'], gpu=False)

reader = load_ocr()

def limpiar_monto(texto):
    numeros = re.sub(r'[^\d]', '', texto)
    return int(numeros) if numeros else 0

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
        st.session_state.v_data["recla"].append({"valor": "0", "tipo": "PPD"})
    
    items_recla = []
    total_siniestros = 0
    for i, item in enumerate(st.session_state.v_data["recla"]):
        col1, col2 = st.columns(2)
        with col1:
            v = st.text_input(f"Monto {i+1}", value=item['valor'], key=f"recla_v_{i}")
        with col2:
            t = st.text_input(f"Tipo {i+1}", value=item['tipo'], key=f"recla_t_{i}")
        
        monto_num = limpiar_monto(v)
        total_siniestros += monto_num
        items_recla.append({"valor": v, "tipo": t})

    if st.session_state.v_data["recla"]:
        st.divider()
        st.markdown(f"### 💰 Total Siniestros\n**$ {total_siniestros:,.0f}**")

# --- CUERPO PRINCIPAL ---
st.title("🚗 Analizador Técnico de Historial - Colombia")

st.info("🔗 Consultas Oficiales en Colombia")
c1, c2, c3 = st.columns(3)
with c1: 
    st.link_button("🌐 RUNT NACIONAL", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo", use_container_width=True)
    st.link_button("🚓 ANTECEDENTES POLICÍA", "https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx", use_container_width=True)
    st.link_button("⚖️ RAMA JUDICIAL (Procesos)", "https://consultaprocesos.ramajudicial.gov.co/Consulta/NumeroRadicacion", use_container_width=True)
with c2: 
    st.link_button("🚦 SIMIT (Multas)", "https://www.fcm.org.co/simit/#/estado-cuenta", use_container_width=True)
    st.link_button("🏢 MOVILIDAD BOGOTÁ", "https://www.movilidadbogota.gov.co/web/SIMIT", use_container_width=True)
    st.link_button("📸 FOTOMULTAS MEDELLÍN", "https://www.medellin.gov.co/es/secretaria-de-movilidad/consultas-en-linea/", use_container_width=True)
with c3: 
    st.link_button("📊 FASECOLDA (Siniestros)", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx", use_container_width=True)
    st.link_button("🏦 IMPUESTOS (Hacienda)", "https://oficinavirtual.shd.gov.co/OficinaVirtual/login.html", use_container_width=True)
    st.link_button("🛠️ ADUANAS (DIAN - Importación)", "https://www.dian.gov.co/aduanas/Paginas/Inicio.aspx", use_container_width=True)

st.divider()

col_info, col_img = st.columns([1.2, 1])

with col_info:
    st.subheader("🚥 Historial SIMIT (Comparendos)")
    txt_simit = st.text_area("Pega aquí el texto de la consulta del SIMIT:", height=150)
    
    multas_detectadas = []
    if txt_simit:
        montos = re.findall(r'\$\s?[\d\.,]{5,}', txt_simit)
        if montos:
            with st.expander("👁️ Ver Multas Extraídas", expanded=True):
                for m in list(set(montos)):
                    st.write(f"• {m}")
                    multas_detectadas.append(m)

with col_img:
    st.subheader("📸 Escaneo de Evidencia")
    archivo = st.file_uploader("Subir foto de RUNT / Fasecolda", type=["jpg", "png", "jpeg"])
    
    if archivo:
        if st
