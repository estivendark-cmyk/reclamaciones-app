import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

st.set_page_config(page_title="Generador de Reclamaciones Pro", layout="wide")

st.title("📑 Generador de Reportes Profesionales")

uploaded_file = st.file_uploader("Sube la imagen de la reclamación", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    img_data = get_image_base64(uploaded_file)
    
    # DATOS EXTRAÍDOS DE LA IMAGEN DE REFERENCIA
    datos = {
        "placa": "KCM702",
        "motor": "2ZR2P51433",
        "chasis": "9BRKZAAG9P0628447",
        "marca": "TOYOTA",
        "modelo": "2023",
        "clase": "CAMIONETA PASAJ.",
        "tipo": "COROLLA CROSS SE-G HYBRID TP 1800",
        "asegurado": "FERNANDEZ LOPEZ, ADRIANA",
        "cedula": "31629822",
        "tipo_doc": "CÉDULA DE CIUDADANÍA",
        "valor_reclamacion": "$ 5.467.111,00",
        "valor_asegurado": "$ 14.260.000.000,00",
        "historial": [
            {"cia": "ALLIANZ", "placa": "KCM702", "desde": "13/06/2025", "hasta": "13/06/2026", "estado": "VIGENTE"},
            {"cia": "ALLIANZ", "placa": "KCM702", "desde": "13/06/2022", "hasta": "13/06/2025", "estado": "CADUCADA"}
        ]
    }

    if st.button("GENERAR PDF CON FORMATO COMPLETO"):
        html_template = f"""
        <html>
        <head>
            <style>
                @page {{ size: A4; margin: 0.5cm; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }}
                .header {{ background-color: #001e4d; color: white; padding: 25px; text-align: left; }}
                .yellow-bar {{ background-color: #ffcc00; color: #001e4d; padding: 10px; font-weight: bold; text-align: center; font-size: 13px; }}
                
                .container {{ padding: 20px; }}
                .section-box {{ background: white; border: 1px solid #ced4da; border-radius: 8px; margin-bottom: 15px; padding: 0; overflow: hidden; }}
                .section-header {{ background-color: #e9ecef; padding: 8px 15px; font-weight: bold; color: #001e4d; border-bottom: 1px solid #ced4da; font-size: 12px; }}
                
                .grid-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
                .grid-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
                .label {{ font-weight: bold; color: #495057; width: 35%; }}
                
                .historial-table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
                .historial-table th {{ background-color: #001e4d; color: white; padding: 8px; text-align: left; }}
                .historial-table td {{ padding: 8px; border-bottom: 1px solid #dee2e6; }}
                
                .foto-evidencia {{ width: 100%; max-height: 250px; object-fit: contain; background: #eee; border-radius: 5px; }}
                .valor-red {{ color: #d32f2f; font-weight: bold; font-size: 14px; }}
                
                .footer-banner {{ background-color: #001e4d; color: white; padding: 15px; position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 11px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin:0; font-size: 24px;">¿NECESITAS CONSULTAR RECLAMACIONES?</h1>
                <p style="margin:5px 0 0 0;">Conoce el historial de tu vehículo al instante</p>
            </div>
            <div class="yellow-bar">TU ACCESO A TU INFORMACIÓN, TU RESPONSABILIDAD.</div>

            <div class="container">
                <div style="display: flex; gap: 15px;">
                    <!-- Columna Izquierda: Imagen -->
                    <div style="width: 45%;">
                        <div class="section-box">
                            <div class="section-header">1 SUBE LA IMAGEN DE LA RECLAMACIÓN</div>
                            <div style="padding:10px; text-align:center;">
                                <img src="data:image/png;base64,{img_data}" class="foto-evidencia">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Columna Derecha: Datos Vehículo -->
                    <div style="width: 55%;">
                        <div class="section-box">
                            <div class="section-header">2 INFORMACIÓN EXTRAÍDA DE LA IMAGEN</div>
                            <table class="grid-table">
                                <tr><td class="label">Placa:</td><td>{datos['placa']}</td></tr>
                                <tr><td class="label">Motor:</td><td>{datos['motor']}</td></tr>
                                <tr><td class="label">Marca/Modelo:</td><td>{datos['marca']} / {datos['modelo']}</td></tr>
                                <tr><td class="label">Tipo:</td><td>{datos['tipo']}</td></tr>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Datos del Asegurado y Resumen -->
                <div style="display: flex; gap: 15px;">
                    <div class="section-box" style="width: 50%;">
                        <div class="section-header">👤 INFORMACIÓN DEL ASEGURADO</div>
                        <table class="grid-table">
                            <tr><td class="label">Nombre:</td><td>{datos['asegurado']}</td></tr>
                            <tr><td class="label">Cédula:</td><td>{datos['cedula']}</td></tr>
                        </table>
                    </div>
                    <div class="section-box" style="width: 50%;">
                        <div class="section-header">💰 RESUMEN ECONÓMICO</div>
                        <table class="grid-table">
                            <tr><td class="label">Valor Asegurado:</td><td>{datos['valor_asegurado']}</td></tr>
                            <tr><td class="label">Total Reclamación:</td><td class="valor-red">{datos['valor_reclamacion']}</td></tr>
                        </table>
                    </div>
                </div>

                <!-- Tabla de Historial -->
                <div class="section-box">
                    <div class="section-header">📋 HISTORIAL DE RECLAMACIONES</div>
                    <table class="historial-table">
                        <thead>
                            <tr>
                                <th>Compañía</th>
                                <th>Placa</th>
                                <th>Desde</th>
                                <th>Hasta</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {" ".join([f"<tr><td>{h['cia']}</td><td>{h['placa']}</td><td>{h['desde']}</td><td>{h['hasta']}</td><td>{h['estado']}</td></tr>" for h in datos['historial']])}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="footer-banner">
                CONSULTA YA Y COMPRA CON CONFIANZA<br>
                Más transparencia, más seguridad para ti.
            </div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            HTML(string=html_template).write_pdf(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("📥 DESCARGAR PDF FORMATO REFERENCIA", f, f"Reporte_{datos['placa']}.pdf")
        os.unlink(tmp.name)