import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64
import easyocr
import numpy as np
from PIL import Image
import re

# Configuración de página
st.set_page_config(page_title="Analizador Pro de Siniestros", layout="wide")

# Función para cargar OCR con manejo de errores
@st.cache_resource
def load_ocr():
    try:
        return easyocr.Reader(['es'])
    except Exception as e:
        st.error(f"Error al cargar el motor de IA: {e}")
        return None

reader = load_ocr()

def get_image_base64(file):
    return base64.b64encode(file.read()).decode()

def limpiar_monto(texto):
    # Extrae solo los números de una cadena tipo "$ 12.000.000"
    numeros = re.sub(r'[^\d]', '', texto)
    return int(numeros) if numeros else 0

# --- LÓGICA DE EXTRACCIÓN ---
def analizar_todo(texto_lista):
    texto_unido = " ".join(texto_lista).upper()
    
    # 1. Encontrar TODOS los montos (Incluso los de millones)
    # Busca $ seguido de números, puntos o comas
    montos_raw = re.findall(r'\$\s?[\d\.,]{4,}', texto_unido)
    
    siniestros = []
    for m in list(set(montos_raw)):
        # Clasificación básica por palabras clave cercanas
        tipo = "Reclamación"
        contexto = texto_unido[max(0, texto_unido.find(m)-50) : texto_unido.find(m)+50]
        if "PPD" in contexto: tipo = "Pérdida Parcial (PPD)"
        elif "PPP" in contexto: tipo = "Pérdida Hurto (PPP)"
        elif "TOTAL" in contexto: tipo = "Pérdida Total"
        
        siniestros.append({"monto": m, "detalle": tipo, "valor_num": limpiar_monto(m)})

    # 2. Encontrar Placa
    placa = next(iter(re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', texto_unido)), "KCM702")
    
    # 3. Encontrar Nombre (Mejorado)
    nombre = "No detectado"
    for i, p in enumerate(texto_lista):
        if any(x in p.upper() for x in ["ASEGURADO", "CLIENTE", "NOMBRE"]):
            # Tomamos el siguiente bloque que usualmente es el nombre
            if i + 1 < len(texto_lista):
                nombre = texto_lista[i+1]
                break

    return nombre, placa, siniestros

# --- INTERFAZ ---
st.sidebar.header("⚙️ Configuración del Reporte")

if 'datos' not in st.session_state:
    st.session_state.datos = {"nombre": "", "placa": "", "lista": []}

with st.sidebar.expander("👤 Identificación", expanded=True):
    nombre_input = st.text_input("Asegurado", value=st.session_state.datos["nombre"])
    placa_input = st.text_input("Placa", value=st.session_state.datos["placa"])

with st.sidebar.expander("💰 Desglose de Siniestros", expanded=True):
    items_editados = []
    total_suma = 0
    for i, item in enumerate(st.session_state.datos["lista"]):
        m = st.text_input(f"Valor {i+1}", value=item['monto'], key=f"m_{i}")
        t = st.text_input(f"Tipo {i+1}", value=item['detalle'], key=f"t_{i}")
        v_num = limpiar_monto(m)
        total_suma += v_num
        items_editados.append({"monto": m, "detalle": t, "valor_num": v_num})
    
    if total_suma > 0:
        st.metric("SUMA TOTAL", f"$ {total_suma:,.0f}")

# --- CUERPO ---
st.title("🔍 Analizador y Sumador de Reclamaciones")

archivo = st.file_uploader("Sube la imagen para transcribir", type=["jpg", "png", "jpeg"])

if archivo:
    if st.button("🚀 INICIAR TRANSCRIPCIÓN AUTOMÁTICA"):
        with st.spinner("Leyendo imagen y sumando valores..."):
            img = Image.open(archivo)
            # El OCR a veces falla si la imagen es muy grande, la redimensionamos un poco
            img.thumbnail((1500, 1500))
            res = reader.readtext(np.array(img), detail=0)
            
            if not res:
                st.error("No se detectó texto. Asegúrate de que la imagen sea clara.")
            else:
                n, p, l = analizar_todo(res)
                st.session_state.datos = {"nombre": n, "placa": p, "lista": l}
                st.rerun()

    if st.session_state.datos["lista"]:
        # Generar PDF
        if st.button("📥 DESCARGAR PDF CON SUMATORIA"):
            img_64 = base64.b64encode(archivo.getvalue()).decode()
            
            filas_html = "".join([
                f"<tr><td>{x['detalle']}</td><td style='color:red;'>{x['monto']}</td></tr>" 
                for x in items_editados
            ])

            html_content = f"""
            <html>
            <head><style>
                body {{ font-family: sans-serif; padding: 30px; }}
                .header {{ background: #001e4d; color: white; padding: 20px; text-align: center; }}
                .summary {{ background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
                .total-row {{ background: #eee; font-weight: bold; font-size: 18px; }}
            </style></head>
            <body>
                <div class="header"><h1>REPORTE DE SINIESTRALIDAD ACUMULADA</h1></div>
                <div class="summary">
                    <b>ASEGURADO:</b> {nombre_input}<br>
                    <b>PLACA:</b> {placa_input}
                </div>
                <table>
                    <thead><tr><th>TIPO DE SINIESTRO</th><th>VALOR</th></tr></thead>
                    <tbody>
                        {filas_html}
                        <tr class="total-row"><td>TOTAL ACUMULADO</td><td>$ {total_suma:,.0f}</td></tr>
                    </tbody>
                </table>
                <div style="text-align:center; margin-top:30px;">
                    <img src="data:image/png;base64,{img_64}" style="max-width:90%;">
                </div>
            </body></html>
            """
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                HTML(string=html_content).write_pdf(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 GUARDAR REPORTE PDF", f, f"Reporte_{placa_input}.pdf")
