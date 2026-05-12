import streamlit as st
from fpdf import FPDF
import tempfile
import re
import google.generativeai as genai
from PIL import Image
import os

# --- CONFIGURACIÓN DE GEMINI ---
# Tu API KEY integrada
API_KEY = "AIzaSyBsBYSlQ-alP6716JKKii-yXNRXXs8efyc"

# Forzamos la configuración inicial
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Error en configuración de API: {e}")

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

# Enlaces Colombia
st.info("🔗 Consultas de Tránsito Colombia")
c1, c2, c3 = st.columns(3)
with c1:
    st.link_button("🌐 RUNT", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo", use_container_width=True)
with c2:
    st.link_button("🚦 SIMIT", "https://www.fcm.org.co/simit/#/estado-cuenta", use_container_width=True)
with c3:
    st.link_button("📊 FASECOLDA", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx", use_container_width=True)

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
            # CAMBIO CLAVE: Usamos 'gemini-pro-vision' como respaldo si flash falla, 
            # pero intentamos gemini-1.5-flash de forma directa.
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            with st.spinner("La IA está leyendo el documento..."):
                img = Image.open(archivo)
                prompt = "Extrae la PLACA y el VIN de este documento. Responde exactamente así: PLACA: XXX000 | VIN: 12345678901234567"
                
                # Intentamos la generación
                response = model.generate_content([prompt, img])
                res_text = response.text.upper()
                
                p = re.search(r'PLACA:\s?([A-Z0-9]+)', res_text)
                v = re.search(r'VIN:\s?([A-Z0-9]+)', res_text)
                
                if p: st.session_state.v_data["placa"] = p.group(1)
                if v: st.session_state.v_data["vin"] = v.group(1)
                
                st.success("✅ Lectura completada.")
                st.rerun()
        except Exception as e:
            st.error(f"Error de API: {e}")
            st.warning("⚠️ Intenta refrescar la página o verifica que la API Key esté habilitada para 'Generative Language API'.")

    if archivo: st.image(archivo, use_container_width=True)

# --- GENERACIÓN DE REPORTE ---
st.divider()
if st.button("📥 GENERAR PDF FINAL"):
    if not archivo:
        st.error("Adjunta una imagen para el reporte.")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(0, 30, 77); pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 15, "REPORTE TÉCNICO DE INSPECCIÓN", ln=True, align='C')
        
        pdf.set_text_color(0, 0, 0); pdf.ln(10); pdf.set_font("Arial", 'B', 11)
        pdf.cell(95, 9, f"PLACA: {placa_f}", border=1)
        pdf.cell(95, 9, f"VIN: {vin_f}", border=1, ln=True)
        pdf.cell(95, 9, f"SOAT: {f_soat}", border=1)
        pdf.cell(95, 9, f"TECNO: {f_tecno}", border=1, ln=True)
        
        pdf.ln(5); pdf.set_fill_color(230, 230, 230); pdf.cell(190, 9, "RECLAMACIONES DE ASEGURADORA", ln=True, fill=True, border=1)
        pdf.set_font("Arial", '', 10)
        for r in st.session_state.v_data["recla"]:
            pdf.cell(140, 8, r['tipo'], border=1); pdf.cell(50, 8, r['valor'], border=1, ln=True)
        
        pdf.ln(10)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            Image.open(archivo).convert('RGB').save(tmp.name)
            pdf.image(tmp.name, x=10, w=180)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 DESCARGAR DOCUMENTO PDF", f, f"Inspeccion_{placa_f}.pdf")
            os.unlink(tmp_pdf.name)
