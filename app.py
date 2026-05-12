import streamlit as st
from fpdf import FPDF
import tempfile
import re
import google.generativeai as genai
from PIL import Image
import os

# --- CONFIGURACIÓN DE GEMINI CON TU CLAVE ---
API_KEY = "AIzaSyBsBYSlQ-alP6716JKKii-yXNRXXs8efyc" 
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Validador Técnico CDA", layout="wide")

def limpiar_monto(texto):
    numeros = re.sub(r'[^\d]', '', str(texto))
    return int(numeros) if numeros else 0

# --- BARRA LATERAL ---
st.sidebar.header("📋 Identificación Vehicular")
if 'v_data' not in st.session_state:
    st.session_state.v_data = {"placa": "", "vin": "", "recla": []}

with st.sidebar:
    placa_f = st.text_input("📍 Placa Actual", value=st.session_state.v_data["placa"])
    vin_f = st.text_input("🆔 VIN / Chasis", value=st.session_state.v_data["vin"])
    st.divider()
    f_soat = st.date_input("Vencimiento SOAT")
    f_tecno = st.date_input("Vencimiento Tecno")
    
    st.subheader("🛡️ Registro de Siniestros")
    if st.button("➕ Agregar Fila"):
        st.session_state.v_data["recla"].append({"valor": "0", "tipo": "PPD"})
    
    total_siniestros = 0
    for i, item in enumerate(st.session_state.v_data["recla"]):
        c1, c2 = st.columns(2)
        with c1: v = st.text_input(f"Monto {i+1}", value=item['valor'], key=f"v_{i}")
        with c2: t = st.text_input(f"Tipo {i+1}", value=item['tipo'], key=f"t_{i}")
        total_siniestros += limpiar_monto(v)
        st.session_state.v_data["recla"][i] = {"valor": v, "tipo": t}

    if total_siniestros > 0:
        st.metric("💰 TOTAL RECLAMACIONES", f"$ {total_siniestros:,.0f}")

# --- CUERPO PRINCIPAL ---
st.title("🚗 Analizador Técnico Automotriz (Gemini AI)")

st.info("🔗 Consultas de Tránsito Colombia")
c1, c2, c3 = st.columns(3)
with c1:
    st.link_button("🌐 RUNT", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo", use_container_width=True)
    st.link_button("🚓 ANTECEDENTES POLICÍA", "https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx", use_container_width=True)
with c2:
    st.link_button("🚦 SIMIT", "https://www.fcm.org.co/simit/#/estado-cuenta", use_container_width=True)
    st.link_button("⚖️ RAMA JUDICIAL", "https://consultaprocesos.ramajudicial.gov.co/Consulta/NumeroRadicacion", use_container_width=True)
with c3:
    st.link_button("📊 FASECOLDA", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx", use_container_width=True)
    st.link_button("🏦 HACIENDA (Impuestos)", "https://oficinavirtual.shd.gov.co/OficinaVirtual/login.html", use_container_width=True)

st.divider()

c_info, c_img = st.columns([1.2, 1])

with c_info:
    st.subheader("🚥 Pegado Manual SIMIT")
    txt_simit = st.text_area("Pega aquí el detalle de multas:", height=150)
    multas = re.findall(r'\$\s?[\d\.,]{5,}', txt_simit) if txt_simit else []

with c_img:
    st.subheader("📸 Escaneo de Imagen")
    archivo = st.file_uploader("Sube foto de tarjeta o reporte", type=["jpg", "png", "jpeg"])
    
    if archivo and st.button("🔍 ANALIZAR CON IA"):
        try:
