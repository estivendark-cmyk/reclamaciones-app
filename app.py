import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64
import re

st.set_page_config(page_title="Gestor Integral de Siniestros", layout="wide")

# --- FUNCIONES DE APOYO ---
def limpiar_y_sumar(monto_str):
    numeros = re.sub(r'[^\d]', '', monto_str)
    return int(numeros) if numeros else 0

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

# --- BARRA LATERAL (DATOS Y RECLAMACIONES) ---
st.sidebar.header("📋 Datos del Informe")

with st.sidebar.expander("👤 Información del Cliente", expanded=True):
    nombre_asegurado = st.text_input("Nombre Completo", value="ADRIANA FERNANDEZ LOPEZ")
    placa = st.text_input("Placa", value="KCM702")

with st.sidebar.expander("💰 Desglose de Siniestros", expanded=True):
    if 'siniestros' not in st.session_state:
        st.session_state.siniestros = [{"valor": "$ 0", "tipo": "PPD"}]
    
    if st.button("➕ Agregar Reclamación"):
        st.session_state.siniestros.append({"valor": "$ 0", "tipo": "Reclamación"})

    items_finales = []
    total_acumulado = 0
    
    for i, item in enumerate(st.session_state.siniestros):
        st.markdown(f"**Siniestro #{i+1}**")
        v = st.text_input(f"Valor", value=item['valor'], key=f"v_{i}")
        t = st.text_input(f"Tipo (PPD/PPP/RCE)", value=item['tipo'], key=f"t_{i}")
        
        num_v = limpiar_y_sumar(v)
        total_acumulado += num_v
        items_finales.append({"valor": v, "tipo": t})
    
    st.divider()
    st.metric("SUMA TOTAL", f"$ {total_acumulado:,.0f}")

# --- CUERPO PRINCIPAL ---
st.title("🚗 Sistema de Validación y Soporte")

# Botones de Consulta Pública
c1, c2, c3 = st.columns(3)
with c1: st.link_button("🌐 RUNT", "https://www.runt.com.co/consultaCiudadana/#/consultaVehiculo")
with c2: st.link_button("🚦 SIMIT", "https://www.fcm.org.co/simit/#/estado-cuenta")
with c3: st.link_button("📊 FASECOLDA", "https://noticias.fasecolda.com/fasecolda/GuiaValores/Buscar.aspx")

st.divider()

col_txt, col_img = st.columns(2)

with col_txt:
    st.subheader("📄 Transcripción de Información")
    txt_soat = st.text_area("Información SOAT (Copia y pega aquí):", height=100, placeholder="Vigencia, entidad...")
    txt_tecno = st.text_area("Revisión Tecnomecánica (Copia y pega aquí):", height=100)
    txt_simit = st.text_area("Estado de Multas SIMIT (Copia y pega aquí):", height=100)

with col_img:
    st.subheader("📸 Evidencia de Imagen")
    archivo = st.file_uploader("Sube el pantallazo o foto del soporte", type=["jpg", "png", "jpeg"])
    if archivo:
        st.image(archivo, caption="Evidencia cargada", use_container_width=True)

# --- GENERACIÓN DEL DOCUMENTO ---
if st.button("📥 GENERAR Y DESCARGAR REPORTE PDF"):
    if not archivo:
        st.error("Debes subir una imagen de evidencia para generar el PDF.")
    else:
        with st.spinner("Compilando reporte..."):
            img_data = base64.b64encode(archivo.getvalue()).decode()
            
            # Construir filas de la tabla de siniestros
            filas_siniestros = "".join([
                f"<tr><td>{s['tipo']}</td><td style='color:red; font-weight:bold;'>{s['valor']}</td></tr>" 
                for s in items_finales
            ])

            html_content = f"""
            <html>
            <head><style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px; color: #333; }}
                .header {{ background: #001e4d; color: white; padding: 20px; text-align: center; }}
                .section-title {{ background: #eee; padding: 8px; font-weight: bold; margin-top: 20px; border-left: 5px solid #ffcc00; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                td, th {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                .total {{ background: #f2f2f2; font-weight: bold; font-size: 16px; }}
                .text-block {{ font-size: 11px; white-space: pre-wrap; padding: 10px; background: #fafafa; border: 1px solid #eee; }}
            </style></head>
            <body>
                <div class="header"><h1>INFORME TÉCNICO DE VALIDACIÓN</h1></div>
                
                <p><b>Asegurado:</b> {nombre_asegurado} | <b>Placa:</b> {placa}</p>

                <div class="section-title">HISTORIAL DE RECLAMACIONES Y VALORES</div>
                <table>
                    <thead><tr><th>TIPO DE SINIESTRO</th><th>VALOR PAGADO</th></tr></thead>
                    <tbody>
                        {filas_siniestros}
                        <tr class="total"><td>SUMA TOTAL VALIDADA</td><td>$ {total_acumulado:,.0f}</td></tr>
                    </tbody>
                </table>

                <div class="section-title">TRANSCRIPCIÓN DE DOCUMENTOS (SIMIT/SOAT/TECNO)</div>
                <div class="text-block">
                    <b>DETALLE SOAT:</b><br>{txt_soat if txt_soat else "No registrado"}<br><br>
                    <b>DETALLE TECNOMECÁNICA:</b><br>{txt_tecno if txt_tecno else "No registrado"}<br><br>
                    <b>ESTADO SIMIT:</b><br>{txt_simit if txt_simit else "No registrado"}
                </div>

                <div style="page-break-before: always; text-align: center;">
                    <div class="section-title">SOPORTE FOTOGRÁFICO</div>
                    <img src="data:image/png;base64,{img_data}" style="max-width: 95%; margin-top: 20px; border: 1px solid #ddd;">
                </div>
            </body></html>
            """
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                HTML(string=html_content).write_pdf(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 DESCARGAR INFORME FINAL PDF", f, f"Reporte_{placa}.pdf")
            os.unlink(tmp.name)
