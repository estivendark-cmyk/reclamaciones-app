import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Automotriz VIN", layout="wide")

# Estilo personalizado para emular diseño automotriz en la app
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTextArea textarea { font-family: monospace; }
    .report-title { font-size: 32px; font-weight: bold; color: #E63946; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DEL PDF ---
class AutomotivePDF(FPDF):
    def header(self):
        # Fondo oscuro para el encabezado
        self.set_fill_color(30, 30, 30)
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_font('Arial', 'B', 24)
        self.set_text_color(230, 57, 70) # Rojo automotriz
        self.cell(0, 20, 'REPORTE TECNICO DE RECLAMACION', ln=True, align='L')
        
        self.set_font('Arial', 'I', 10)
        self.set_text_color(255, 255, 255)
        self.cell(0, -5, f'Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True, align='R')
        self.ln(20)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')
        # Líneas de firma
        self.line(30, 270, 80, 270)
        self.line(130, 270, 180, 270)
        self.text(45, 275, "FIRMA TECNICO")
        self.text(145, 275, "FIRMA CLIENTE")

def generate_pdf(vin, reclamaciones):
    pdf = AutomotivePDF()
    pdf.add_page()
    
    # Cuadro del VIN
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "IDENTIFICACION DEL VEHICULO (VIN):", ln=True, fill=True)
    
    pdf.set_font('Courier', 'B', 20)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 15, f" {vin.upper()}", ln=True, border='B')
    
    pdf.ln(10)
    
    # Cuadro de Reclamaciones
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "DETALLE DE RECLAMACIONES:", ln=True)
    
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 8, reclamaciones)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ DE USUARIO (STREAMLIT) ---

# Sidebar (Apartado Izquierdo)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3202/3202926.png", width=100)
st.sidebar.title("Panel de Control")
st.sidebar.markdown("---")

vin_input = st.sidebar.text_input("PLACA / VIN", placeholder="Ej: 1HGCM82...", help="Ingrese los 17 dígitos del VIN")
reclamaciones_input = st.sidebar.text_area("RECLAMACIONES", placeholder="Describa los fallos detectados...", height=200)

st.sidebar.markdown("---")

# Botón de descarga en el sidebar
if vin_input and reclamaciones_input:
    pdf_bytes = generate_pdf(vin_input, reclamaciones_input)
    st.sidebar.download_button(
        label="📥 DESCARGAR REPORTE PDF",
        data=pdf_bytes,
        file_name=f"Reporte_{vin_input}.pdf",
        mime="application/pdf"
    )
else:
    st.sidebar.warning("Complete el VIN y las reclamaciones para habilitar la descarga.")

# Área Principal (Vista Previa)
st.markdown('<p class="report-title">Vista Previa del Documento</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Datos del Vehículo")
    st.info(f"**VIN:** {vin_input if vin_input else 'Pendiente...'}")

with col2:
    st.subheader("Estado")
    if vin_input and reclamaciones_input:
        st.success("Listo para exportar")
    else:
        st.error("Datos incompletos")

st.markdown("---")
st.subheader("Contenido de la Reclamación")
st.write(reclamaciones_input if reclamaciones_input else "Esperando descripción...")
