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
    .error-box {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
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
    .shopify-link {
        background: #1a1a2e;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        font-weight: 600;
        margin-top: 10px;
    }
    .shopify-link:hover {
        background: #16213e;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🛒 Product Creator</h1>
    <p>Crea productos en <strong>Shopify</strong> como borrador en segundos</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <strong>📋 Cómo funciona:</strong><br>
    1️⃣ Llena el formulario con la información del producto<br>
    2️⃣ Dale clic a <strong>"Crear en Shopify"</strong><br>
    3️⃣ ¡Listo! El producto se crea automáticamente como borrador 🚀
</div>
""", unsafe_allow_html=True)

# ─── SHOPIFY API CONFIG ───
def get_shopify_config():
    """Lee configuración de Shopify desde secrets o retorna None."""
    try:
        return {
            "shop_url": st.secrets["SHOPIFY_SHOP_URL"],
            "access_token": st.secrets["SHOPIFY_ACCESS_TOKEN"],
            "api_version": st.secrets.get("SHOPIFY_API_VERSION", "2025-01"),
        }
    except KeyError:
        return None


def create_product_in_shopify(config, title, body_html, vendor, price, cost, weight_kg,
                              length_cm, width_cm, height_cm, product_type, tags, raw_description):
    """
    Crea un producto en Shopify Admin API como borrador.
    Retorna dict con success, product_id, variant_id, admin_url, error.
    """
    shop_url = config["shop_url"]
    token = config["access_token"]
    version = config["api_version"]
    base_url = f"https://{shop_url}/admin/api/{version}"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }

    # 1. Crear el producto
    product_payload = {
        "product": {
            "title": title,
            "body_html": body_html,
            "vendor": vendor,
            "product_type": product_type,
            "tags": tags,
            "status": "draft",
            "variants": [
                {
                    "price": str(price),
                    "grams": int(weight_kg * 1000),
                    "inventory_management": "shopify",
                    "inventory_quantity": 0,
                    "requires_shipping": True,
                }
            ],
            "metafields": [
                {"namespace": "shipping", "key": "length_cm", "value": str(length_cm), "type": "number_decimal"},
                {"namespace": "shipping", "key": "width_cm", "value": str(width_cm), "type": "number_decimal"},
                {"namespace": "shipping", "key": "height_cm", "value": str(height_cm), "type": "number_decimal"},
                {"namespace": "raw", "key": "description", "value": raw_description, "type": "single_line_text_field"},
            ]
        }
    }

    try:
        resp = requests.post(f"{base_url}/products.json", headers=headers, json=product_payload, timeout=15)
        if resp.status_code not in (200, 201):
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:500]}"}

        data = resp.json()["product"]
        product_id = data["id"]
        variant_id = data["variants"][0]["id"] if data.get("variants") else None

        # 2. Actualizar costo en inventory_item
        if variant_id and cost and cost > 0:
            try:
                # Obtener inventory_item_id
                variant_resp = requests.get(f"{base_url}/variants/{variant_id}.json", headers=headers, timeout=10)
                if variant_resp.status_code == 200:
                    inv_item_id = variant_resp.json()["variant"].get("inventory_item_id")
                    if inv_item_id:
                        cost_payload = {"inventory_item": {"cost": str(cost)}}
                        requests.put(f"{base_url}/inventory_items/{inv_item_id}.json", headers=headers, json=cost_payload, timeout=10)
            except Exception:
                pass  # No crítico

        admin_url = f"https://{shop_url}/admin/products/{product_id}"
        return {
            "success": True,
            "product_id": product_id,
            "variant_id": variant_id,
            "title": title,
            "admin_url": admin_url,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_seo_content(tipo, marca, modelo, description_raw, precio, costo, peso, largo, ancho, alto):
    """
    Genera contenido SEO automáticamente SIN IA.
    Usa templates inteligentes con los datos del producto.
    """
    # Título optimizado
    title = f"{marca} {modelo} — {tipo} | NEBRO"

    # Extraer líneas de la descripción para bullet points
    raw_lines = [line.strip("•- ") for line in description_raw.split("\n") if line.strip() and len(line.strip()) > 3]
    bullets = "\n".join([f"<li>{line}</li>" for line in raw_lines[:8]])

    # Body HTML con SEO básico
    body_html = f"""
<h1>{marca} {modelo} — {tipo}</h1>

<h2>Descripción del Producto</h2>
<p>{description_raw.replace(chr(10), ' ')}</p>

<h2>Características Principales</h2>
<ul>
{bullets}
</ul>

<h2>Especificaciones Técnicas</h2>
<ul>
<li><strong>Marca:</strong> {marca}</li>
<li><strong>Modelo:</strong> {modelo}</li>
<li><strong>Tipo:</strong> {tipo}</li>
<li><strong>Peso de envío:</strong> {peso} kg</li>
<li><strong>Dimensiones:</strong> {largo} × {ancho} × {alto} cm</li>
</ul>

<h2>Contenido del Paquete</h2>
<ul>
<li>1 × {marca} {modelo}</li>
<li>Manual de usuario</li>
</ul>

<p><em>Producto nuevo con garantía. Envío seguro garantizado.</em></p>
""".strip()

    # Tags SEO
    tags = f"{marca}, {modelo}, {tipo}, NEBRO, {marca} {modelo}, {tipo} {marca}"

    # Keywords
    keywords = f"{marca} {modelo}, {tipo} {marca}, comprar {marca} {modelo}, {modelo} precio, {tipo} Mexico"

    return {
        "title": title,
        "body_html": body_html,
        "tags": tags,
        "keywords": keywords,
    }


# ─── FORMULARIO ───
with st.form("product_form", clear_on_submit=True):
    st.markdown('<div class="section-title">📄 Información del Producto</div>', unsafe_allow_html=True)

    description = st.text_area(
        "Descripción del producto *",
        placeholder="Pega aquí toda la información que tengas:\n• Especificaciones del proveedor\n• Características técnicas\n• Contenido de la caja\n• Notas, observaciones, etc.",
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
    submitted = st.form_submit_button("🚀 Crear en Shopify", use_container_width=True, type="primary")


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
        config = get_shopify_config()

        if not config:
            st.markdown("""
            <div class="error-box">
                <h3>🔐 Configuración de Shopify no encontrada</h3>
                <p>Para crear productos automáticamente, debes configurar los <strong>Secrets</strong> de Streamlit Cloud:</p>
                <ol>
                    <li>Ve a tu app en <a href="https://share.streamlit.io" target="_blank">Streamlit Cloud</a></li>
                    <li>Clic en <strong>⋮ → Settings → Secrets</strong></li>
                    <li>Agrega:</li>
                </ol>
                <pre style="background:#1e293b;color:#e2e8f0;padding:10px;border-radius:6px;">
SHOPIFY_SHOP_URL = "nebro-shop.myshopify.com"
SHOPIFY_ACCESS_TOKEN = "shpca_...tu_token..."
SHOPIFY_API_VERSION = "2025-01"
                </pre>
                <p>Luego dale <strong>Reboot app</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.spinner("⏳ Generando contenido SEO y creando producto en Shopify..."):
                # Generar SEO automáticamente
                seo = generate_seo_content(
                    tipo, marca, modelo, description.strip(),
                    precio, costo, peso, largo, ancho, alto
                )

                # Crear en Shopify
                result = create_product_in_shopify(
                    config=config,
                    title=seo["title"],
                    body_html=seo["body_html"],
                    vendor=marca,
                    price=precio,
                    cost=costo,
                    weight_kg=peso,
                    length_cm=largo,
                    width_cm=ancho,
                    height_cm=alto,
                    product_type=tipo,
                    tags=seo["tags"],
                    raw_description=description.strip(),
                )

            if result["success"]:
                st.markdown("""
                <div class="success-box">
                    <h3 style="color:#166534;margin-bottom:0.5rem;">✅ Producto creado exitosamente</h3>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.subheader("📦 Resumen del Producto")
                    st.write(f"**Título:** {result['title']}")
                    st.write(f"**ID:** `{result['product_id']}`")
                    st.write(f"**Variante:** `{result['variant_id']}`")
                    st.write(f"**Precio:** ${precio:,.2f} MXN")
                    st.write(f"**Costo:** ${costo:,.2f} MXN")
                    st.write(f"**Margen:** {((precio - costo) / precio * 100):.1f}%")

                    st.markdown(f"""
                    <a href="{result['admin_url']}" target="_blank" class="shopify-link">
                        🔗 Abrir en Shopify Admin
                    </a>
                    """, unsafe_allow_html=True)

                with col_b:
                    st.subheader("🏷️ SEO Generado")
                    st.write("**Tags:**")
                    st.code(seo["tags"], language="text")
                    st.write("**Keywords:**")
                    st.code(seo["keywords"], language="text")

                with st.expander("📝 Ver descripción HTML generada", expanded=False):
                    st.code(seo["body_html"], language="html")

                # Guardar en session state
                st.session_state["last_created"] = {
                    "product_id": result["product_id"],
                    "title": result["title"],
                    "url": result["admin_url"],
                    "timestamp": datetime.now().isoformat(),
                }

            else:
                st.markdown(f"""
                <div class="error-box">
                    <h3>❌ Error al crear el producto</h3>
                    <p>{result.get('error', 'Error desconocido')}</p>
                    <p>Verifica que el token de Shopify sea válido y tenga permisos de <code>write_products</code>.</p>
                </div>
                """, unsafe_allow_html=True)

# ─── HISTORIAL DE LA SESIÓN ───
if "last_created" in st.session_state:
    with st.expander("🕐 Último producto creado", expanded=False):
        st.json(st.session_state["last_created"])
