import streamlit as st
import json
import requests
from datetime import datetime

st.set_page_config(
    page_title="Product Creator — Shopify",
    page_icon="🛒",
    layout="centered",
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .main-header h1 {
        color: #1e3a8a;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #64748b;
        font-size: 1.1rem;
    }
    .info-box {
        background: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    .success-box {
        background: #dcfce7;
        border-left: 4px solid #22c55e;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
    .stForm {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #334155;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🛒 Product Creator</h1>
    <p>Crea productos en <strong>Shopify</strong> como borrador con descripciones SEO optimizadas</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <strong>📋 Cómo funciona:</strong><br>
    1️⃣ Llena el formulario con la información del producto<br>
    2️⃣ Dale clic a <strong>"Generar y Preparar"</strong><br>
    3️⃣ Copia el resumen generado y envíaselo a <strong>Kimi Claw</strong><br>
    4️⃣ Kimi genera la descripción SEO y crea el borrador en Shopify 🚀
</div>
""", unsafe_allow_html=True)

# ─── FORMULARIO ───
with st.form("product_form", clear_on_submit=False):
    st.markdown('<div class="section-title">📄 Información del Producto</div>', unsafe_allow_html=True)
    
    description = st.text_area(
        "Descripción desordenada del producto *",
        placeholder="Pega aquí toda la información que tengas:\n• Especificaciones del proveedor\n• Características técnicas\n• Contenido de la caja\n• Notas, observaciones, etc.\nNo importa el orden ni el formato.",
        height=180,
    )
    
    col1, col2 = st.columns(2)
    with col1:
        tipo_options = ["", "Cargador", "Bocina", "Power Bank", "Audífonos", "Smartwatch", "Linterna", "Cable / Accesorio", "Soporte", "Otro (escribir)"]
        tipo = st.selectbox("Tipo de producto *", tipo_options)
        if tipo == "Otro (escribir)":
            tipo_custom = st.text_input("Escribe el tipo de producto:", placeholder="Ej: Adaptador, Funda, Teclado...")
            tipo = tipo_custom.strip() if tipo_custom else ""
    with col2:
        marca_options = ["", "Moreka", "G-tide", "FOL", "NEBRO", "Otro (escribir)"]
        marca = st.selectbox("Marca *", marca_options)
        if marca == "Otro (escribir)":
            marca_custom = st.text_input("Escribe la marca:", placeholder="Ej: Samsung, Apple, Xiaomi...")
            marca = marca_custom.strip() if marca_custom else ""
    
    modelo = st.text_input("Modelo *", placeholder="Ej: CP005, M-337, L22, etc.")
    
    st.markdown('<div class="section-title">💰 Precios y Costos</div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    with col3:
        precio = st.number_input("Precio de venta (MXN) *", min_value=0.0, step=0.01, format="%.2f")
    with col4:
        costo = st.number_input("Costo del producto (MXN) *", min_value=0.0, step=0.01, format="%.2f")
    
    st.markdown('<div class="section-title">📦 Envío — Medidas y Peso</div>', unsafe_allow_html=True)
    
    peso = st.number_input("Peso del envío (kg) *", min_value=0.0, step=0.001, format="%.3f", help="Peso total del paquete para envío")
    
    col5, col6, col7 = st.columns(3)
    with col5:
        largo = st.number_input("Largo (cm) *", min_value=0.0, step=0.1, format="%.1f")
    with col6:
        ancho = st.number_input("Ancho (cm) *", min_value=0.0, step=0.1, format="%.1f")
    with col7:
        alto = st.number_input("Alto (cm) *", min_value=0.0, step=0.1, format="%.1f")
    
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("✨ Generar y Preparar", use_container_width=True, type="primary")

# ─── PROCESAR ───
if submitted:
    # Validación
    required_fields = {
        "Descripción": description,
        "Tipo": tipo,
        "Marca": marca,
        "Modelo": modelo,
        "Precio": precio,
        "Costo": costo,
        "Peso": peso,
        "Largo": largo,
        "Ancho": ancho,
        "Alto": alto,
    }
    
    empty = [k for k, v in required_fields.items() if not v or (isinstance(v, str) and v.strip() == "")]
    
    if empty:
        st.error(f"❌ Faltan campos obligatorios: {', '.join(empty)}")
    else:
        # Construir payload
        payload = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "marca": marca,
            "modelo": modelo,
            "descripcion_raw": description.strip(),
            "precio_venta": round(precio, 2),
            "costo_producto": round(costo, 2),
            "peso_kg": round(peso, 3),
            "largo_cm": round(largo, 1),
            "ancho_cm": round(ancho, 1),
            "alto_cm": round(alto, 1),
        }
        
        # Generar prompt SEO
        prompt_seo = f"""Como experto e-commerce, marketing digital y SEO te pido que me ayudes a hacer la publicación la {tipo} {marca} {modelo}, CON LENGUAJE empático te pido busques la compra de los lectores, favor de no usar emojis, que no tenga más de 500 palabras, separa en párrafos H1, H2, H3, que optimicen el SEO de la mejor manera tanto para buscadores como market places como amazon y mercado libre y has un listado al final de la publicación de las características técnicas y el contenido del producto y también las palabras claves SEO, utiliza la siguiente información para crear nuestra publicación:

{description.strip()}"""
        
        # Guardar en session state para persistencia dentro de la sesión
        st.session_state["last_payload"] = payload
        st.session_state["last_prompt"] = prompt_seo
        
        st.markdown("---")
        st.markdown("""
        <div class="success-box">
            <h3 style="color:#166534;margin-bottom:0.5rem;">✅ Datos listos para procesar</h3>
            <p style="color:#15803d;">Copia el resumen de abajo y envíaselo a <strong>Kimi Claw</strong> para generar la descripción SEO.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ─── RESUMEN ───
        st.subheader("📋 Resumen del Producto")
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.json(payload)
        with col_b:
            st.metric("Margen", f"{((precio - costo) / precio * 100):.1f}%", f"${precio - costo:.2f}")
            st.metric("Volumen", f"{largo * ancho * alto:.0f} cm³")
            st.metric("Peso", f"{peso:.3f} kg")
        
        # ─── PROMPT SEO ───
        st.subheader("📝 Prompt SEO para Kimi Claw")
        st.info("Copia este prompt y envíalo a Kimi Claw. Él generará la descripción optimizada y creará el borrador en Shopify.")
        st.text_area("Prompt (clic para copiar)", value=prompt_seo, height=250, label_visibility="collapsed")
        
        # Botón copiar
        st.code(prompt_seo, language="text")
        
        # Botón descargar JSON
        json_str = json.dumps(payload, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Descargar JSON del producto",
            data=json_str,
            file_name=f"producto_{marca.lower()}_{modelo.lower().replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )
        
        # ─── WEBHOOK (opcional) ───
        webhook_url = st.secrets.get("WEBHOOK_URL", "")
        if webhook_url:
            with st.spinner("Enviando datos al servidor..."):
                try:
                    resp = requests.post(webhook_url, json=payload, timeout=10)
                    if resp.status_code == 200:
                        st.success("🚀 Datos enviados automáticamente a Kimi Claw. Será notificado.")
                    else:
                        st.warning(f"⚠️ Webhook respondió {resp.status_code}. Copia el prompt manualmente.")
                except Exception as e:
                    st.warning(f"⚠️ No se pudo enviar automáticamente: {e}")
        else:
            st.info("💡 **Siguiente paso:** Copia el prompt de arriba y envíalo a Kimi Claw. Él procesará todo y creará el borrador en Shopify.")

# ─── HISTORIAL DE LA SESIÓN ───
if "last_payload" in st.session_state:
    with st.expander("🕐 Ver último producto generado", expanded=False):
        st.json(st.session_state["last_payload"])
