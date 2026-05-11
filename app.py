import streamlit as st
from fpdf import FPDF
import tempfile
import re
import google.generativeai as genai
from PIL import Image
import os

# CONFIGURACIÓN DE GEMINI
# Reemplaza "TU_API_KEY_AQUÍ" con la clave que sacaste de AI Studio
API_KEY = "AIzaSyBsBYSlQ-alP6716JKKii-yXNRXXs8efyc" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Validador CDA con Gemini AI", layout="wide")

def limpiar_monto(texto):
    numeros = re.sub(r'[^\d]', '', str(texto))
    return int(numeros) if numeros else 0

# --- BARRA LATERAL ---
st.sidebar.header("📋 Datos del Vehículo")

if 'v_data' not in st.session_state:
    st.session_state.v_data = {"placa": "", "vin": "", "recla": []}

with st.sidebar:
    placa_f = st.text_input("📍 Placa", value=st.session_state.v_data["placa"])
    vin_f = st.text_input("🆔 VIN / Chasis", value=st.session_state.v_data["vin"])
    
    st.divider()
    st.subheader("🗓️ Vencimientos")
    f_soat = st.date_input("Vencimiento SOAT")
    f_tecno = st.date_input("Vencimiento Tecno")
    
    st.divider()
    st.subheader("🛡️ Siniestros")
    if st.button("➕ Añadir Hallazgo"):
        st.session_state.v_data["recla"].append({"valor": "0", "tipo": "PPD"})
    
    total_siniestros = 0
    for i, item in enumerate(st.session_state.v_data["recla"]):
        c1, c2 = st.columns(2)
        with c1: v = st.text_input(f"Monto {i+1}", value=item['valor'], key=f"v_{i}")
        with c2: t = st.text_input(f"Tipo {i+1}", value=item['tipo'], key=f"t_{i}")
        total_siniestros += limpiar_monto(v)
        st.session_state.v_data["recla"][i] = {"valor": v, "tipo": t}

    if st.session_state.v_data["recla"]:
        st.divider()
        st.metric("💰 TOTAL SINIESTROS", f"$ {total_siniestros:,.0f}")

# --- CUERPO PRINCIPAL ---
st.title("🚀 Analizador Técnico con Gemini AI")

st.info("🔗 Consultas Rápidas Colombia")
col_links = st.columns(3)
with col_links[0]:
    st.link_button("🌐 RUNT", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo", use_container_width=True)
    st.link_button("🚓 POLICÍA", "https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx", use_container_width=True)
with col_links[1]:
    st.link_button("🚦 SIMIT", "https://www.fcm.org.co/simit/#/estado-cuenta", use_container_width=True)
    st.link_button("🏢 MOVILIDAD BOGOTÁ", "https://www.movilidadbogota.gov.co/web/SIMIT", use_container_width=True)
with col_links[2]:
    st.link_button("📊 FASECOLDA", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx", use_container_width=True)
    st.link_button("🏦 HACIENDA (Impuestos)", "https://oficinavirtual.shd.gov.co/OficinaVirtual/login.html", use_container_width=True)

st.divider()

c_info, c_img = st.columns([1.2, 1])

with c_info:
    st.subheader("🚥 Pegado de Datos SIMIT")
    txt_simit = st.text_area("Pega el historial de multas aquí:", height=150)
    multas = re.findall(r'\$\s?[\d\.,]{5,}', txt_simit) if txt_simit else []
    if multas:
        with st.expander("👁️ Multas Detectadas"):
            for m in list(set(multas)): st.write(f"• {m}")

with c_img:
    st.subheader("📸 Escaneo Inteligente")
    archivo = st.file_uploader("Subir foto de evidencia", type=["jpg", "png", "jpeg"])
    
    if archivo and st.button("🔍 ESCANEAR CON GEMINI"):
        with st.spinner("Gemini analizando imagen..."):
            img = Image.open(archivo)
            # Prompt para Gemini
            prompt = "Extrae la PLACA (formato colombiano) y el VIN (17 caracteres) de esta imagen. Responde solo en este formato: PLACA: XXX000, VIN: 1234567890ABCDEFG"
            
            response = model.generate_content([prompt, img])
            res_text = response.text.upper()
            
            # Extraer con Regex de la respuesta de Gemini
            p = re.search(r'PLACA:\s?([A-Z0-9]+)', res_text)
            v = re.search(r'VIN:\s?([A-Z0-9]+)', res_text)
            
            if p: st.session_state.v_data["placa"] = p.group(1)
            if v: st.session_state.v_data["vin"] = v.group(1)
            st.rerun()
    if archivo: st.image(archivo, use_container_width=True)

# --- PDF ---
if st.button("📥 GENERAR REPORTE PDF"):
    if not archivo:
        st.error("Sube una imagen primero.")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(0, 30, 77); pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 15, "REPORTE TÉCNICO DE SINIESTROS", ln=True, align='C')
        
        pdf.set_text_color(0, 0, 0); pdf.ln(10); pdf.set_font("Arial", 'B', 11)
        pdf.cell(95, 9, f"PLACA: {placa_f}", border=1)
        pdf.cell(95, 9, f"VIN: {vin_f}", border=1, ln=True)
        pdf.cell(95, 9, f"VENCIMIENTO SOAT: {f_soat}", border=1)
        pdf.cell(95, 9, f"VENCIMIENTO TECNO: {f_tecno}", border=1, ln=True)
        
        pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.cell(190, 9, "RECLAMACIONES", ln=True, fill=True, border=1)
        pdf.set_font("Arial", '', 10)
        for r in st.session_state.v_data["recla"]:
            pdf.cell(140, 8, r['tipo'], border=1); pdf.cell(50, 8, r['valor'], border=1, ln=True)
            
        if multas:
            pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 9, "COMPARENDOS", ln=True, fill=True, border=1)
            pdf.set_font("Arial", '', 10)
            for m in list(set(multas)):
                pdf.cell(140, 8, "Multa detectada", border=1); pdf.cell(50, 8, m, border=1, ln=True)

        pdf.ln(10)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            Image.open(archivo).convert('RGB').save(tmp.name)
            pdf.image(tmp.name, x=10, w=180)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 DESCARGAR PDF", f, f"Reporte_{placa_f}.pdf")
