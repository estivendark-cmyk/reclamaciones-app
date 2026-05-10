import streamlit as st
from weasyprint import HTML
import tempfile
import os
import base64
import numpy as np
from PIL import Image
import re

# Intentar importar EasyOCR de forma segura
try:
    import easyocr
    OCR_DISPONIBLE = True
except ImportError:
    OCR_DISPONIBLE = False

st.set_page_config(page_title="Validador de Siniestros Pro", layout="wide")

@st.cache_resource
def load_ocr():
    if OCR_DISPONIBLE:
        try:
            # Forzamos el uso de CPU para evitar errores de memoria en la nube
            return easyocr.Reader(['es'], gpu=False)
        except:
            return None
    return None

reader = load_ocr()

def limpiar_monto(texto):
    numeros = re.sub(r'[^\d]', '', texto)
    return int(numeros) if numeros else 0

# --- LÓGICA DE EXTRACCIÓN ---
def analizar_datos(texto_lista):
    texto_unido = " ".join(texto_lista).upper()
    montos_raw = re.findall(r'\$\s?[\d\.,]{4,}', texto_unido)
    
    siniestros = []
    for m in list(set(montos_raw)):
        tipo = "Reclamación Detectada"
        if "PPD" in texto_unido: tipo = "Pérdida Parcial (PPD)"
        elif "PPP" in texto_unido: tipo = "Pérdida Hurto (PPP)"
        siniestros.append({"monto": m, "detalle": tipo, "valor_num": limpiar_monto(m)})

    placa = next(iter(re.findall(r'[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]', texto_unido)), "KCM702")
    return placa, siniestros

# --- INTERFAZ ---
st.title("📊 Analizador y Sumador de Historial")

if 'datos' not in st.session_state:
    st.session_state.datos = {"placa": "KCM702", "lista": []}

# Sidebar para edición manual y sumatoria
with st.sidebar:
    st.header("⚙️ Panel de Control")
    placa_f = st.text_input("Placa", value=st.session_state.datos["placa"])
    
    st.subheader("Lista de Siniestros")
    items_finales = []
    suma_total = 0
    
    # Botón para añadir siniestros manualmente si la IA falla
    if st.button("➕ Añadir Fila Manual"):
        st.session_state.datos["lista"].append({"monto": "$ 0", "detalle": "Nueva Reclamación", "valor_num": 0})

    for i, item in enumerate(st.session_state.datos["lista"]):
        col1, col2 = st.columns(2)
        with col1:
            m = st.text_input(f"Monto {i+1}", value=item['monto'], key=f"m_{i}")
        with col2:
            t = st.text_input(f"Tipo {i+1}", value=item['detalle'], key=f"t_{i}")
        
        v_n = limpiar_monto(m)
        suma_total += v_n
        items_finales.append({"monto": m, "detalle": t, "valor_num": v_n})
    
    st.divider()
    st.metric("SUMA TOTAL", f"$ {suma_total:,.0f}")

# Cuerpo Principal
archivo = st.file_uploader("Sube el pantallazo del historial", type=["jpg", "png", "jpeg"])

if archivo:
    if st.button("🚀 EXTRAER Y TRANSCRIBIR"):
        if reader:
            with st.spinner("IA analizando imagen..."):
                img = Image.open(archivo).convert('RGB')
                res = reader.readtext(np.array(img), detail=0)
                p, l = analizar_datos(res)
                st.session_state.datos = {"placa": p, "lista": l}
                st.rerun()
        else:
            st.error("El motor de IA no pudo iniciarse en el servidor. Usa el botón 'Añadir Fila Manual' en la izquierda.")

    if items_finales:
        if st.button("📥 GENERAR PDF CON SUMATORIA"):
            img_b64 = base64.b64encode(archivo.getvalue()).decode()
            filas = "".join([f"<tr><td>{x['detalle']}</td><td style='color:red;'>{x['monto']}</td></tr>" for x in items_finales])
            
            html = f"""
            <html><head><style>
                body {{ font-family: sans-serif; padding: 20px; }}
                .header {{ background: #001e4d; color: white; padding: 15px; text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                td, th {{ border: 1px solid #ddd; padding: 10px; }}
                .total {{ background: #eee; font-weight: bold; font-size: 16px; }}
            </style></head>
            <body>
                <div class="header"><h2>REPORTE DE SINIESTRALIDAD ACUMULADA</h2></div>
                <p><b>PLACA:</b> {placa_f}</p>
                <table>
                    <thead><tr><th>TIPO</th><th>VALOR</th></tr></thead>
                    <tbody>{filas}
                    <tr class="total"><td>SUMA TOTAL ACUMULADA</td><td>$ {suma_total:,.0f}</td></tr>
                    </tbody>
                </table>
                <div style="text-align:center; margin-top:20px;">
                    <img src="data:image/png;base64,{img_b64}" style="max-width:85%;">
                </div>
            </body></html>"""
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                HTML(string=html).write_pdf(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 DESCARGAR PDF", f, f"Siniestros_{placa_f}.pdf")
