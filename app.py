import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64

# Función para cargar imágenes locales (como tu logo del gorila)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

st.set_page_config(page_title="Portal de Reclamaciones", layout="centered")

# --- INTERFAZ DE USUARIO ---
st.markdown("<h2 style='text-align: center; color: #001e4d;'>🚀 Generador de Reportes Premium</h2>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Sube la evidencia fotográfica", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img_evidencia = base64.b64encode(uploaded_file.read()).decode()
    
    # Aquí puedes poner la ruta de tu logo si lo subes a GitHub
    # logo_base64 = get_base64_of_bin_file("logo_gorila.png") 

    if st.button("✨ GENERAR REPORTE DE LUJO"):
        html_template = f"""
        <html>
        <head>
            <style>
                @page {{ size: A4; margin: 0; }}
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5; color: #333; margin: 0; }}
                
                /* Encabezado Elegante */
                .header {{ background: linear-gradient(135deg, #001e4d 0%, #003380 100%); color: white; padding: 40px 20px; text-align: center; border-bottom: 5px solid #ffcc00; }}
                
                .container {{ padding: 30px; }}
                
                /* Estilo de Tarjetas Profesionales */
                .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 6px solid #001e4d; }}
                .card-title {{ font-size: 14px; font-weight: bold; color: #001e4d; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }}
                
                .data-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }}
                .label {{ font-weight: 600; color: #666; font-size: 12px; }}
                .value {{ font-weight: 500; color: #111; font-size: 12px; }}
                
                /* Foto de evidencia con estilo */
                .foto-frame {{ border-radius: 10px; width: 100%; max-height: 300px; object-fit: cover; border: 2px solid #ddd; }}
                
                .highlight-value {{ color: #d32f2f; font-weight: bold; font-size: 16px; }}
                
                .footer {{ text-align: center; padding: 20px; font-size: 10px; color: #777; background: #fff; position: absolute; bottom: 0; width: 100%; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin:0; font-size: 28px;">REPORTE DE RECLAMACIÓN</h1>
                <p style="opacity: 0.8; margin-top: 5px;">Certificado de Inspección de Historial Vehicular</p>
            </div>

            <div class="container">
                <div style="display: flex; gap: 20px;">
                    <div style="flex: 1;">
                        <div class="card">
                            <div class="card-title">🚗 Detalles del Vehículo</div>
                            <div class="data-row"><span class="label">PLACA</span><span class="value">KCM702</span></div>
                            <div class="data-row"><span class="label">MARCA</span><span class="value">TOYOTA</span></div>
                            <div class="data-row"><span class="label">MODELO</span><span class="value">2023</span></div>
                            <div class="data-row"><span class="label">TIPO</span><span class="value">COROLLA CROSS SE-G</span></div>
                        </div>
                    </div>
                    <div style="flex: 1;">
                        <div class="card">
                            <div class="card-title">📸 Evidencia Visual</div>
                            <img src="data:image/png;base64,{img_evidencia}" class="foto-frame">
                        </div>
                    </div>
                </div>

                <div class="card" style="border-left-color: #ffcc00;">
                    <div class="card-title">👤 Información del Asegurado</div>
                    <div class="data-row"><span class="label">NOMBRE COMPLETO</span><span class="value">FERNANDEZ LOPEZ, ADRIANA</span></div>
                    <div class="data-row"><span class="label">DOCUMENTO</span><span class="value">C.C. 31.629.822</span></div>
                </div>

                <div class="card">
                    <div class="card-title">💰 Resumen Financiero</div>
                    <div class="data-row"><span class="label">VALOR ASEGURADO</span><span class="value">$ 14.260.000.000,00</span></div>
                    <div class="data-row"><span class="label">TOTAL RECLAMACIÓN</span><span class="value highlight-value">$ 5.467.111,00</span></div>
                </div>
            </div>

            <div class="footer">
                Documento generado electrónicamente. La información contenida es de carácter informativo.
            </div>
        </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            HTML(string=html_template).write_pdf(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("📥 DESCARGAR REPORTE PROFESIONAL", f, "Reporte_Premium.pdf")
        os.unlink(tmp.name)
