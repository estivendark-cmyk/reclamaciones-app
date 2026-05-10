import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64

# Función para convertir la imagen subida a formato base64 para el PDF
def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

st.set_page_config(page_title="Gestor de Reclamaciones", layout="wide")

# --- BARRA LATERAL: PANEL DE TRANSCRIPCIÓN ---
st.sidebar.header("📝 Panel de Transcripción")

with st.sidebar.expander("🚗 Datos del Vehículo", expanded=True):
    placa = st.text_input("Placa", value="KCM702")
    marca_linea = st.text_input("Marca / Línea", value="TOYOTA COROLLA CROSS")
    modelo = st.text_input("Modelo (Año)", value="2023")
    chasis = st.text_input("Chasis / VIN", value="9BRKZAAG9P0628447")

with st.sidebar.expander("👤 Datos del Asegurado"):
    nombre_asegurado = st.text_input("Nombre Completo", value="ADRIANA FERNANDEZ LOPEZ")
    id_asegurado = st.text_input("Identificación (C.C.)", value="31.629.822")

with st.sidebar.expander("📊 Reporte de Reclamaciones o Siniestros"):
    valor_recla = st.text_input("MONTO RECLAMACIÓN", value="$ 5.467.111,00")
    valor_aseg = st.text_input("Valor Asegurado", value="$ 14.260.000.000,00")
    estado_siniestro = st.selectbox("Estado del Siniestro", ["PAGADO", "EN PROCESO", "OBJETADO", "VIGENTE"])

with st.sidebar.expander("📝 Notas Adicionales"):
    observaciones = st.text_area("Comentarios Informativos", "Información transcrita de bases de datos oficiales...")

# --- CUERPO PRINCIPAL ---
st.markdown("<h2 style='color: #001e4d; text-align: center;'>📋 Sistema de Soporte Informativo</h2>", unsafe_allow_html=True)

# Herramientas Rápidas
col_a, col_b = st.columns(2)
with col_a:
    st.link_button("🌐 Abrir RUNT (Consulta Placa)", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo")
with col_b:
    st.link_button("📊 Abrir Guía Fasecolda", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx")

st.divider()

# Subida de Imagen
uploaded_file = st.file_uploader("📸 Sube la imagen de evidencia (RUNT o Reclamación)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Mostramos la imagen en la app para verificar
    st.image(uploaded_file, caption="Evidencia cargada", width=400)
    
    if st.button("🚀 GENERAR REPORTE COMPLETO"):
        img_data = get_image_base64(uploaded_file)
        
        # HTML del PDF con el diseño profesional
        html_template = f"""
        <html>
        <head>
            <style>
                @page {{ size: A4; margin: 0; }}
                body {{ font-family: 'Helvetica', Arial, sans-serif; margin: 0; padding: 0; color: #333; }}
                .header {{ background-color: #001e4d; color: white; padding: 35px; text-align: center; }}
                .yellow-banner {{ background-color: #ffcc00; color: #001e4d; padding: 12px; text-align: center; font-weight: bold; font-size: 13px; }}
                .container {{ padding: 30px; }}
                .card {{ border: 1px solid #dee2e6; border-radius: 10px; margin-bottom: 20px; overflow: hidden; background: white; }}
                .card-header {{ background-color: #f1f3f5; padding: 10px 15px; font-weight: bold; color: #001e4d; border-bottom: 1px solid #dee2e6; }}
                .data-table {{ width: 100%; border-collapse: collapse; }}
                .data-table td {{ padding: 10px 15px; border-bottom: 1px solid #f8f9fa; font-size: 12px; }}
                .label {{ font-weight: bold; color: #666; width: 40%; }}
                .value {{ font-weight: 500; }}
                .price {{ color: #d32f2f; font-weight: bold; font-size: 16px; }}
                .img-container {{ text-align: center; padding: 20px; }}
                .img-container img {{ max-width: 90%; max-height: 400px; border: 1px solid #ddd; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; font-size: 10px; color: #aaa; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin:0;">SOPORTE INFORMATIVO PROFESIONAL</h1>
                <p style="margin:5px 0 0 0;">Reporte de Reclamaciones y Datos de Vehículo</p>
            </div>
            <div class="yellow-banner">TRANSCRIPCIÓN DE INFORMACIÓN REGISTRADA - DOCUMENTO DE CONSULTA</div>

            <div class="container">
                <div style="display: flex; gap: 20px;">
                    <div style="width: 50%;">
                        <div class="card">
                            <div class="card-header">DATOS DEL VEHÍCULO</div>
                            <table class="data-table">
                                <tr><td class="label">PLACA:</td><td class="value">{placa}</td></tr>
                                <tr><td class="label">MARCA/LÍNEA:</td><td class="value">{marca_linea}</td></tr>
                                <tr><td class="label">AÑO MODELO:</td><td class="value">{modelo}</td></tr>
                                <tr><td class="label">VIN/CHASIS:</td><td class="value">{chasis}</td></tr>
                            </table>
                        </div>
                        <div class="card">
                            <div class="card-header">DATOS DEL ASEGURADO</div>
                            <table class="data-table">
                                <tr><td class="label">NOMBRE:</td><td class="value">{nombre_asegurado}</td></tr>
                                <tr><td class="label">ID:</td><td class="value">{id_asegurado}</td></tr>
                            </table>
                        </div>
                    </div>
                    <div style="width: 50%;">
                        <div class="card">
                            <div class="card-header">REPORTE DE RECLAMACIONES O SINIESTROS</div>
                            <table class="data-table">
                                <tr><td class="label">VALOR RECLAMACIÓN:</td><td class="value price">{valor_recla}</td></tr>
                                <tr><td class="label">ESTADO:</td><td class="value">{estado_siniestro}</td></tr>
                                <tr><td class="label">VALOR ASEGURADO:</td><td class="value">{valor_aseg}</td></tr>
                            </table>
                        </div>
                        <div class="img-container">
                            <img src="data:image/png;base64,{img_data}">
                            <p style="font-size: 9px; color: #999;">Evidencia Fotográfica de Soporte</p>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">NOTAS Y OBSERVACIONES</div>
                    <div style="padding:15px; font-size: 11px; color: #555; line-height: 1.5;">
                        {observaciones}
                    </div>
                </div>
            </div>

            <div class="footer">
                Este reporte tiene fines informativos. La información ha sido transcrita fielmente de las fuentes disponibles.
            </div>
        </body>
        </html>
        """
        
        # Generación del PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            HTML(string=html_template).write_pdf(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("📥 DESCARGAR REPORTE PROFESIONAL", f, f"Reporte_{placa}.pdf")
        os.unlink(tmp.name)
else:
    st.warning("⚠️ Por favor, sube una imagen para habilitar la generación del reporte.")
