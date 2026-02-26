import streamlit as st
from PIL import Image
from fpdf import FPDF
import os
import smtplib
from email.message import EmailMessage
from pyairtable import Api
import cloudinary
import cloudinary.uploader

# ==========================================
# 🔧 1. CONFIGURACIÓN DE CREDENCIALES
# ==========================================

# --- AIRTABLE ---
AIRTABLE_PAT = "patsqGyB1HPsSS9zm.4fa6af42946edf4dfb5a61af75f61e3670bfd0ddac0febedd6d94ab0e01343ba"
AIRTABLE_BASE_ID = "appY6cQfQdXpmMlwD"
AIRTABLE_TABLE_NAME = "Cotizaciones"

# --- CLOUDINARY (Para alojar PDF y Fotos) ---
CLOUD_NAME = "dgowkt8nm"
API_KEY = "937683936737541"
API_SECRET = "3NcKjXbQAubzYRajbLHKsJ_Y-_U"

# Inicializar Cloudinary solo si ya pusiste tus datos
# Inicializar Cloudinary correctamente
cloudinary.config(
    cloud_name = CLOUD_NAME,
    api_key = API_KEY,
    api_secret = API_SECRET,
    secure = True
)
# ==========================================
# ⚙️ 2. FUNCIONES PRINCIPALES
# ==========================================

def obtener_siguiente_folio():
    archivo_folio = "folio.txt"
    if not os.path.exists(archivo_folio):
        folio_num = 1
    else:
        with open(archivo_folio, "r") as f:
            contenido = f.read().strip()
            folio_num = int(contenido) + 1 if contenido.isdigit() else 1
            
    with open(archivo_folio, "w") as f:
        f.write(str(folio_num))
    return f"{folio_num:04d}"

def enviar_correo(correo_destino, nombre_cliente, pdf_bytes, folio):
    remitente = "tu_correo@gmail.com" # Cambia por tu correo
    password = "tu_contraseña_de_aplicacion" # Cambia por tu contraseña de app
    
    msg = EmailMessage()
    msg['Subject'] = f'Cotización Plaga Clean - Folio {folio}'
    msg['From'] = remitente
    msg['To'] = correo_destino
    msg.set_content(f"Hola {nombre_cliente},\n\nAdjunto encontrarás la cotización solicitada para nuestro servicio de fumigación (Folio: {folio}).\n\nQuedamos a tus órdenes.\n\nSaludos,\nEquipo Plaga Clean")
    
    msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f"Cotizacion_{folio}_PlagaClean.pdf")
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        return False

def crear_pdf(folio, nombre, correo, direccion, metros, plagas, subtotal, iva, total):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(130, 10, "Plaga Clean", ln=0)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(60, 10, f"Folio: {folio}", ln=1, align="R")
    pdf.cell(0, 5, "", ln=1) 
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Datos del Cliente", ln=1)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"Nombre: {nombre}", ln=1)
    pdf.cell(0, 6, f"Correo: {correo}", ln=1)
    pdf.multi_cell(0, 6, f"Dirección: {direccion}") 
    pdf.cell(0, 5, "--------------------------------------------------------------------------------", ln=1)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Detalles del Servicio", ln=1)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"Área a tratar: {metros} m2", ln=1)
    plagas_str = ", ".join(plagas)
    pdf.cell(0, 6, f"Plagas identificadas: {plagas_str}", ln=1)
    pdf.cell(0, 5, "--------------------------------------------------------------------------------", ln=1)
    
    pdf.set_font("helvetica", "", 12)
    pdf.cell(130, 8, "Subtotal:", ln=0, align="R")
    pdf.cell(60, 8, f"${subtotal:,.2f} MXN", ln=1, align="R")
    pdf.cell(130, 8, "IVA (16%):", ln=0, align="R")
    pdf.cell(60, 10, f"${total:,.2f} MXN", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(130, 10, "Total Estimado:", ln=0, align="R")
    pdf.cell(60, 10, f"${total:,.2f} MXN", ln=1, align="R")
    
    return bytes(pdf.output())

# ==========================================
# 🖥️ 3. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================

st.set_page_config(page_title="Cotizador Plaga Clean", page_icon="🛡️", layout="centered", initial_sidebar_state="collapsed")
st.title("🛡️ Cotizador Plaga Clean")

# --- SECCIÓN 1: CLIENTE ---
st.subheader("1. Datos del Cliente")
col_nombre, col_correo = st.columns(2)
with col_nombre:
    cliente_nombre = st.text_input("Nombre Completo")
with col_correo:
    cliente_correo = st.text_input("Correo Electrónico")
cliente_direccion = st.text_area("Dirección del Servicio")

estatus_cotizacion = st.selectbox("Estatus de la Cotización", ["Enviada", "En espera", "Agendada", "Pagada", "Perdida"], index=1)

# --- SECCIÓN 2: SERVICIO ---
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
    if not plagas or not cliente_nombre:
        st.warning("⚠️ Nombre del cliente y al menos un tipo de plaga son obligatorios.")
    else:
        if 'folio_actual' not in st.session_state:
            st.session_state['folio_actual'] = obtener_siguiente_folio()
            
        base_calculo = precio_base + (metros_cuadrados * precio_por_m2)
        multiplicador_maximo = max([multiplicadores_plaga[p] for p in plagas])
        
        subtotal = base_calculo * multiplicador_maximo
        iva = subtotal * 0.16
        total_final = subtotal + iva
        
        st.session_state.update({
            'subtotal': subtotal, 'iva': iva, 'total': total_final, 'metros': metros_cuadrados,
            'plagas': plagas, 'nombre': cliente_nombre, 'correo': cliente_correo, 'direccion': cliente_direccion
        })
        
        pdf_bytes = crear_pdf(
            st.session_state['folio_actual'], cliente_nombre, cliente_correo, 
            cliente_direccion, metros_cuadrados, plagas, subtotal, iva, total_final
        )
        st.session_state['pdf_bytes'] = pdf_bytes

        # --- SUBIR ARCHIVOS A CLOUDINARY ---
        pdf_url = ""
        fotos_urls = []
        
        if CLOUD_NAME != "TU_CLOUD_NAME":
            with st.spinner("Subiendo evidencias a la nube..."):
                try:
                    # Guardar y subir PDF temporalmente
                    temp_pdf = f"Cotizacion_{st.session_state['folio_actual']}.pdf"
                    with open(temp_pdf, "wb") as f:
                        f.write(pdf_bytes)
                    res_pdf = cloudinary.uploader.upload(temp_pdf, resource_type="raw")
                    pdf_url = res_pdf["secure_url"]
                    os.remove(temp_pdf)
                    
                    # Guardar y subir Fotos
                    if fotos:
                        for idx, foto in enumerate(fotos):
                            temp_img = f"temp_img_{idx}.jpg"
                            with open(temp_img, "wb") as f:
                                f.write(foto.getvalue())
                            res_img = cloudinary.uploader.upload(temp_img)
                            fotos_urls.append({"url": res_img["secure_url"]})
                            os.remove(temp_img)
                except Exception as e:
                    st.warning(f"Error al subir archivos a la nube: {e}")

        # --- ENVIAR A AIRTABLE ---
        if AIRTABLE_PAT != "TU_TOKEN_PAT_AQUI":
            with st.spinner("Guardando registro en Airtable..."):
                try:
                    api = Api(AIRTABLE_PAT)
                    tabla = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
                    
                    nuevo_registro = {
                        "Folio": st.session_state['folio_actual'],
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
                    
                    # Adjuntar URLs si existen
                    if pdf_url: nuevo_registro["PDF_Cotizacion"] = [{"url": pdf_url}]
                    if fotos_urls: nuevo_registro["Fotos_Evidencia"] = fotos_urls
                    
                    tabla.create(nuevo_registro)
                    st.success("✅ ¡Registro y evidencias guardados exitosamente en Airtable!")
                except Exception as e:
                    st.error(f"❌ Error al conectar con Airtable: {e}")

# ==========================================
# 📊 5. RESULTADOS Y DESCARGAS
# ==========================================

if 'total' in st.session_state:
    st.divider()
    st.markdown(f"### 📋 Resumen - Folio: {st.session_state['folio_actual']}")
    
    col_sub, col_iva, col_tot = st.columns(3)
    col_sub.metric("Subtotal", f"${st.session_state['subtotal']:,.2f}")
    col_iva.metric("IVA (16%)", f"${st.session_state['iva']:,.2f}")
    col_tot.metric("Total", f"${st.session_state['total']:,.2f}")
    
    st.divider()
    col_descarga, col_correo_btn = st.columns(2)
    
    with col_descarga:
        st.download_button(
            label="📥 Descargar PDF", data=st.session_state['pdf_bytes'],
            file_name=f"Cotizacion_{st.session_state['folio_actual']}_PlagaClean.pdf",
            mime="application/pdf", use_container_width=True
        )
        
    with col_correo_btn:
        if st.button("✉️ Enviar por Correo al Cliente", use_container_width=True):
            if st.session_state['correo']:
                with st.spinner("Enviando correo..."):
                    if enviar_correo(st.session_state['correo'], st.session_state['nombre'], st.session_state['pdf_bytes'], st.session_state['folio_actual']):
                        st.success("¡Correo enviado correctamente!")
            else:
                st.error("Falta el correo electrónico del cliente.")

    if fotos:
        st.write("📸 **Evidencia capturada:**")
        for foto in fotos:
            img = Image.open(foto)
            st.image(img, use_container_width=True)