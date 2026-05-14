import streamlit as st
import json
import requests
import uuid
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
    2️⃣ Dale clic a <strong>"Generar"</strong><br>
    3️⃣ Kimi Claw genera la descripción SEO y crea el borrador en Shopify automáticamente 🚀<br>
    <em>El producto estará listo en 5-10 minutos.</em>
</div>
""", unsafe_allow_html=True)

# ─── GITHUB QUEUE CONFIG ───
def get_github_config():
    try:
        return {
            "token": st.secrets["GITHUB_TOKEN"],
            "owner": st.secrets.get("GITHUB_OWNER", "morekaoficial-lgtm"),
            "repo": st.secrets.get("GITHUB_REPO", "nebro-product-creator"),
        }
    except KeyError:
        return None


def fetch_queue(config):
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/contents/queue.json"
    headers = {"Authorization": f"token {config['token']}", "Accept": "application/vnd.github.v3+json"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    elif resp.status_code == 404:
        return {"version": "1.0", "items": []}, None
    else:
        st.error(f"Error leyendo cola: HTTP {resp.status_code}")
        return None, None


def push_queue(config, queue_data, sha=None):
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/contents/queue.json"
    headers = {"Authorization": f"token {config['token']}", "Accept": "application/vnd.github.v3+json"}
    import base64
    content = json.dumps(queue_data, ensure_ascii=False, indent=2)
    payload = {
        "message": f"Add product to queue — {datetime.now().isoformat()}",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha
    resp = requests.put(url, headers=headers, json=payload, timeout=15)
    return resp.status_code in (200, 201)


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
    submitted = st.form_submit_button("✨ Generar", use_container_width=True, type="primary")


# ─── PROCESAR ───
if submitted:
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
        config = get_github_config()
        if not config:
            st.error("🔐 Falta configurar GITHUB_TOKEN en los Secrets de Streamlit Cloud.")
        else:
            with st.spinner("⏳ Agregando a la cola de procesamiento..."):
                queue, sha = fetch_queue(config)
                if queue is not None:
                    new_item = {
                        "id": str(uuid.uuid4())[:8],
                        "submitted_at": datetime.now().isoformat(),
                        "status": "pending",
                        "data": {
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
                        },
                        "seo_content": None,
                        "shopify_result": None,
                        "processed_at": None,
                        "error": None,
                    }
                    queue["items"].append(new_item)
                    queue["last_updated"] = datetime.now().isoformat()

                    if push_queue(config, queue, sha):
                        st.markdown(f"""
                        <div class="success-box">
                            <h3 style="color:#166534;margin-bottom:0.5rem;">✅ Producto agregado a la cola</h3>
                            <p><strong>ID:</strong> <code>{new_item['id']}</code></p>
                            <p>Kimi Claw lo procesará automáticamente en breve y creará el borrador en Shopify.</p>
                            <p><em>Puedes cerrar esta página. Te notificaré cuando esté listo.</em></p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.subheader("📋 Resumen del Producto")
                        col_a, col_b = st.columns([2, 1])
                        with col_a:
                            st.json(new_item["data"])
                        with col_b:
                            st.metric("Margen", f"{((precio - costo) / precio * 100):.1f}%", f"${precio - costo:.2f}")
                            st.metric("Volumen", f"{largo * ancho * alto:.0f} cm³")
                    else:
                        st.error("❌ Error al guardar en la cola. Intenta de nuevo.")
                else:
                    st.error("❌ No se pudo leer la cola de productos.")

# ─── HISTORIAL ───
if "last_submitted" in st.session_state:
    with st.expander("🕐 Último producto enviado", expanded=False):
        st.json(st.session_state["last_submitted"])
