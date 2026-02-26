import streamlit as st
from PIL import Image
from fpdf import FPDF
import os
from pyairtable import Api
import cloudinary
import cloudinary.uploader

# ==========================================
# 🔐 1. CONFIGURACIÓN DE SEGURIDAD (SECRETS)
# ==========================================
try:
# Airtable
    AIRTABLE_PAT = st.secrets["AIRTABLE_PAT"]
    AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
    AIRTABLE_TABLE_NAME = "Cotizaciones"

    # Cloudinary
    CLOUD_NAME = st.secrets["CLOUD_NAME"]
    API_KEY = st.secrets["API_KEY"]
    API_SECRET = st.secrets["API_SECRET"]

    # Inicializar Cloudinary
    cloudinary.config(
        cloud_name=CLOUD_NAME, 
        api_key=API_KEY, 
        api_secret=API_SECRET, 
        secure=True
    )
except Exception as e:
    st.error(f"⚠️ Detalle exacto del error: {e}")

# ==========================================
# ⚙️ 2. FUNCIONES DE APOYO
# ==========================================
def obtener_siguiente_folio():
    archivo_folio = "folio.txt"
    if not os.path.exists(archivo_folio):
        folio_num = 1
    else:
        try:
            with open(archivo_folio, "r") as f:
                contenido = f.read().strip()
                folio_num = int(contenido) + 1 if contenido.isdigit() else 1
        except:
            folio_num = 1
    with open(archivo_folio, "w") as f:
        f.write(str(folio_num))
    return f"{folio_num:04d}"

def crear_pdf(folio, nombre, correo, direccion, metros, plagas, subtotal, iva, total):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(130, 10, "Plaga Clean", new_x="RIGHT", new_y="TOP")
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(60, 10, f"Folio: {folio}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.cell(0, 5, "", new_x="LMARGIN", new_y="NEXT") 
    
    # Datos del Cliente
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Datos del Cliente", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"Nombre: {nombre}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Correo: {correo}", new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 6, f"Dirección: {direccion}") 
    pdf.cell(0, 5, "-"*80, new_x="LMARGIN", new_y="NEXT")
    
    # Detalles del Servicio
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Detalles del Servicio", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"Área a tratar: {metros} m2", new_x="LMARGIN", new_y="NEXT")
    plagas_str = ", ".join(plagas)
    pdf.cell(0, 6, f"Plagas identificadas: {plagas_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "-"*80, new_x="LMARGIN", new_y="NEXT")
    
    # Totales
    pdf.set_font("helvetica", "", 12)
    pdf.cell(130, 8, "Subtotal:", align="R")
    pdf.cell(60, 8, f"${subtotal:,.2f} MXN", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.cell(130, 8, "IVA (16%):", align="R")
    pdf.cell(60, 8, f"${iva:,.2f} MXN", new_x="LMARGIN", new_y="NEXT", align="R")
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(130, 10, "Total Estimado:", align="R")
    pdf.cell(60, 10, f"${total:,.2f} MXN", new_x="LMARGIN", new_y="NEXT", align="R")
    
    return bytes(pdf.output())

# ==========================================
# 🖥️ 3. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Cotizador Plaga Clean", page_icon="🛡️", layout="centered")

st.title("🛡️ Cotizador Plaga Clean")

# --- SECCIÓN 1: DATOS DEL CLIENTE ---
st.subheader("1. Datos del Cliente")
col_nombre, col_correo = st.columns(2)
with col_nombre:
    cliente_nombre = st.text_input("Nombre Completo")
with col_correo:
    cliente_correo = st.text_input("Correo Electrónico")
cliente_direccion = st.text_area("Dirección del Servicio")

estatus_cotizacion = st.selectbox(
    "Estatus de la Cotización", 
    ["Enviada", "En espera", "Agendada", "Pagada", "Perdida"],
    index=1
)

# --- SECCIÓN 2: DATOS DEL SERVICIO ---
st.subheader("2. Detalles del Área")
metros_cuadrados = st.number_input("Metros Cuadrados (m²)", min_value=1, value=50, step=10)
plagas = st.multiselect("Tipos de Plaga a tratar", ["Cucarachas", "Hormigas", "Roedores", "Chinches", "Arañas", "Termitas", "Alacranes"])

# --- SECCIÓN 3: EVIDENCIA ---
st.subheader("3. Evidencia")
fotos = st.file_uploader("Sube tus fotografías", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

precio_base = 500.00
precio_por_m2 = 12.50
multiplicadores_plaga = {"Cucarachas": 1.2, "Hormigas": 1.1, "Roedores": 1.5, "Chinches": 1.8, "Arañas": 1.1, "Termitas": 2.5, "Alacranes": 1.4}

st.divider()

# ==========================================
# 🚀 4. LÓGICA DE PROCESAMIENTO
# ==========================================
if st.button("Generar Cotización y Guardar en Airtable", type="primary", use_container_width=True):
    if not plagas:
        st.warning("⚠️ Selecciona al menos un tipo de plaga.")
    elif not cliente_nombre:
        st.warning("⚠️ El nombre del cliente es obligatorio.")
    else:
        folio_actual = obtener_siguiente_folio()
            
        base_calculo = precio_base + (metros_cuadrados * precio_por_m2)
        multiplicador_maximo = max([multiplicadores_plaga[p] for p in plagas])
        
        subtotal = base_calculo * multiplicador_maximo
        iva = subtotal * 0.16
        total_final = subtotal + iva
        
        # 1. Generar PDF
        pdf_bytes = crear_pdf(folio_actual, cliente_nombre, cliente_correo, cliente_direccion, metros_cuadrados, plagas, subtotal, iva, total_final)

        # 2. Subir Archivos a Cloudinary
        pdf_url = ""
        fotos_urls = []
        
        with st.spinner("Subiendo evidencias a la nube..."):
            try:
                # Guardar y subir PDF temporalmente
                temp_pdf = f"Cotizacion_{folio_actual}.pdf"
                with open(temp_pdf, "wb") as f:
                    f.write(pdf_bytes)
                res_pdf = cloudinary.uploader.upload(temp_pdf, resource_type="raw")
                pdf_url = res_pdf["secure_url"]
                os.remove(temp_pdf)
                
                # Guardar y subir Fotos
                if fotos:
                    for idx, foto in enumerate(fotos):
                        res_img = cloudinary.uploader.upload(foto.getvalue())
                        fotos_urls.append({"url": res_img["secure_url"]})
            except Exception as e:
                st.warning(f"Error al subir archivos a la nube. Verifica tus Secrets.")

        # 3. Enviar a Airtable
        with st.spinner("Guardando registro en Airtable..."):
            try:
                api = Api(AIRTABLE_PAT)
                tabla = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
                
                nuevo_registro = {
                    "Folio": folio_actual,
                    "Cliente": cliente_nombre,
                    "Correo": cliente_correo,
                    "Dirección": cliente_direccion,
                    "Metros": metros_cuadrados,
                    "Plagas": ", ".join(plagas),
                    "Subtotal": subtotal,
                    "IVA": iva,
                    "Total": total_final,
                    "Status": estatus_cotizacion
                }
                
                if pdf_url: nuevo_registro["PDF_Cotizacion"] = [{"url": pdf_url}]
                if fotos_urls: nuevo_registro["Fotos_Evidencia"] = fotos_urls
                
                tabla.create(nuevo_registro)
                st.success(f"✅ ¡Cotización {folio_actual} guardada exitosamente en Airtable!")
                
                # Mostrar métricas rápidas
                col_sub, col_iva, col_tot = st.columns(3)
                col_sub.metric("Subtotal", f"${subtotal:,.2f}")
                col_iva.metric("IVA (16%)", f"${iva:,.2f}")
                col_tot.metric("Total", f"${total_final:,.2f}")
                
                st.download_button(
                    label="📥 Descargar PDF", 
                    data=pdf_bytes,
                    file_name=f"Cotizacion_{folio_actual}_PlagaClean.pdf",
                    mime="application/pdf", 
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error al conectar con Airtable. Verifica tus Secrets.")
