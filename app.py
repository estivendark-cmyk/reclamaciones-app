import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

st.set_page_config(page_title="Gestor Integral de Reclamaciones", layout="wide")

# --- BARRA LATERAL: PANEL DE TRANSCRIPCIÓN ---
st.sidebar.header("📝 Panel de Transcripción")

with st.sidebar.expander("🚗 Datos del Vehículo", expanded=True):
    # Usamos 'key' para evitar el error de DuplicateElementId
    placa = st.text_input("Placa del Vehículo", value="KCM702", key="input_placa")
    marca_linea = st.text_input("Marca / Línea", value="TOYOTA COROLLA CROSS", key="input_marca")
    modelo = st.text_input("Modelo (Año)", value="2023", key="input_modelo")

with st.sidebar.expander("👤 Datos del Asegurado"):
    nombre_asegurado = st.text_input("Nombre Completo", value="ADRIANA FERNANDEZ LOPEZ", key="input_nombre")
    id_asegurado = st.text_input("Identificación (C.C.)", value="31.629.822", key="input_id")

with st.sidebar.expander("📊 Reporte de Reclamaciones"):
    valor_recla = st.text_input("MONTO RECLAMACIÓN", value="$ 5.467.111,00", key="input_monto")
    estado_siniestro = st.selectbox("Estado", ["PAGADO", "EN PROCESO", "OBJETADO", "VIGENTE"], key="input_estado")

with st.sidebar.expander("🚦 Información SIMIT (Multas)", expanded=True):
    texto_simit = st.text_area("Pega aquí el estado de cuenta del SIMIT:", 
                                placeholder="Ejemplo: No tiene multas pendientes...", key="input_simit")

with st.sidebar.expander("📄 Otros Detalles y Anexos"):
    texto_anexo = st.text_area("Pega aquí cualquier otra información adicional:", key="input_anexo")

# --- CUERPO PRINCIPAL ---
st.markdown("<h2 style='color: #001e4d; text-align: center;'>📋 Sistema de Soporte e Historial SIMIT</h2>", unsafe_allow_html=True)

# Botones de Consulta Externa
c1, c2, c3 = st.columns(3)
with c1:
    st.link_button("🌐 Consultar RUNT", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo")
with c2:
    st.link_button("🚦 Consultar SIMIT", "https://www.fcm.org.co/simit/#/estado-cuenta")
with c3:
    st.link_button("📊 Guía Fasecolda", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx")

st.divider()

uploaded_file = st.file_uploader("📸 Sube la evidencia fotográfica", type=["jpg", "png", "jpeg"], key="uploader_principal")

if uploaded_file:
    st.image(uploaded_file, caption="Evidencia para el reporte", width=400)
    
    if st.button("🚀 GENERAR REPORTE INTEGRAL", key="btn_generar"):
        img_data = get_image_base64(uploaded_file)
        
        html_template = f"""
        <html>
        <head>
            <style>
                @page {{ size: A4; margin: 0; }}
                body {{ font-family: 'Helvetica', sans-serif; margin: 0; padding: 0; color: #333; }}
                .header {{ background-color: #001e4d; color: white; padding: 30px; text-align: center; }}
                .yellow-banner {{ background-color: #ffcc00; color: #001e4d; padding: 10px; text-align: center; font-weight: bold; font-size: 12px; }}
                .container {{ padding: 25px; }}
                .card {{ border: 1px solid #dee2e6; border-radius: 8px; margin-bottom: 15px; overflow: hidden; }}
                .card-header {{ background-color: #f1f3f5; padding: 8px 12px; font-weight: bold; color: #001e4d; border-bottom: 1px solid #dee2e6; }}
                .data-table {{ width: 100%; border-collapse: collapse; }}
                .data-table td {{ padding: 8px 12px; border-bottom: 1px solid #f8f9fa; font-size: 11px; }}
                .price {{ color: #d32f2f; font-weight: bold; font-size: 15px; }}
                .text-box {{ padding: 12px; font-size: 10.5px; color: #444; line-height: 1.5; white-space: pre-wrap; background-color: #fdfdfd; }}
                .footer {{ text-align: center; padding: 15px; font-size: 9px; color: #aaa; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin:0;">SOPORTE INFORMATIVO INTEGRAL</h1>
                <p style="margin:5px 0 0 0;">Reporte Vehicular, Siniestros y SIMIT</p>
            </div>
            <div class="yellow-banner">DOCUMENTO DE CONSULTA INFORMATIVA</div>

            <div class="container">
                <div style="display: flex; gap: 15px;">
                    <div style="width: 50%;">
                        <div class="card">
                            <div class="card-header">DATOS DEL VEHÍCULO Y CLIENTE</div>
                            <table class="data-table">
                                <tr><td style="font-weight:bold;">PLACA:</td><td>{placa}</td></tr>
                                <tr><td style="font-weight:bold;">ASEGURADO:</td><td>{nombre_asegurado}</td></tr>
                                <tr><td style="font-weight:bold;">MARCA/MOD:</td><td>{marca_linea} ({modelo})</td></tr>
                            </table>
                        </div>
                        <div class="card">
                            <div class="card-header">REPORTE DE RECLAMACIÓN</div>
                            <table class="data-table">
                                <tr><td style="font-weight:bold;">VALOR:</td><td class="price">{valor_recla}</td></tr>
                                <tr><td style="font-weight:bold;">ESTADO:</td><td>{estado_siniestro}</td></tr>
                            </table>
                        </div>
                    </div>
                    <div style="width: 50%;">
                        <div class="card" style="height: 100%;">
                            <div class="card-header">EVIDENCIA REGISTRADA</div>
                            <div style="text-align:center; padding:10px;">
                                <img src="data:image/png;base64,{img_data}" style="max-width:100%; max-height:220px; border:1px solid #eee;">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">ESTADO DE CUENTA SIMIT (MULTAS)</div>
                    <div class="text-box">
                        {texto_simit if texto_simit else "No se registra información de multas."}
                    </div>
                </div>

                {f'<div class="card"><div class="card-header">ANEXOS ADICIONALES</div><div class="text-box">{texto_anexo}</div></div>' if texto_anexo else ''}

            </div>
            <div class="footer">Información transcrita para fines de soporte documental informativo.</div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            HTML(string=html_template).write_pdf(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("📥 DESCARGAR REPORTE", f, f"Reporte_{placa}.pdf")
        os.unlink(tmp.name)
else:
    st.info("👋 Sube una imagen para activar la generación del PDF.")
