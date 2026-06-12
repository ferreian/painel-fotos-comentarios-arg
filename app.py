"""
app.py - Panel de Fotos y Comentarios de Campo - Argentina (Home)

Pagina inicial de navegacion. NO carga datos - solo lleva al usuario al
cultivo deseado. Toda la logica vive en pagina_fotos.py (pages/).
"""

import base64

import streamlit as st

from theme import aplicar_tema, page_header, asset_path, bandeira_ar_html

st.set_page_config(
    page_title="Fotos y Comentarios · Argentina",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_tema()
st.markdown("""
<style>
.jaum-header > img { height: 78px !important; }
/* Botón "Abrir" (st.page_link) con aspecto de botón verde dentro del card */
[data-testid="stPageLink"] { margin-top: 4px; }
[data-testid="stPageLink"] a {
    background: #E9F7EF !important;
    border: 1px solid #A9DFBF !important;
    border-radius: 8px !important;
    padding: 6px 12px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    justify-content: center !important;
    width: 100% !important;
    transition: all .2s !important;
}
[data-testid="stPageLink"] a, [data-testid="stPageLink"] a * { color: #1E8449 !important; }
[data-testid="stPageLink"] a:hover { background: #27AE60 !important; border-color: #27AE60 !important; }
[data-testid="stPageLink"] a:hover, [data-testid="stPageLink"] a:hover * { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

page_header(
    "Fotos y Comentarios de Campo",
    "Registros fotográficos y observaciones de las evaluaciones · Stine Argentina",
    bandeira=bandeira_ar_html(),
)

# Layout: texto + cards (izquierda, más angosta) | ilustración grande (derecha)
col_esq, col_dir = st.columns([2, 3], gap="large")

with col_esq:
    st.markdown("""
<div style="margin-top:1rem;">
  <p style="font-size:15px;color:#1A1A1A;line-height:1.7;">
    Galería de fotos y comentarios registrados por los responsables en campo.
    Elija el cultivo para visualizar los registros.
  </p>
</div>
<div style="margin:0.8rem 0 0.5rem;">
  <p style="font-size:12px;font-weight:600;color:#6B7280;text-transform:uppercase;
            letter-spacing:0.07em;margin:0 0 4px;">Cultivos</p>
  <h2 style="font-size:1.3rem;font-weight:700;color:#1A1A1A;margin:0;">
    ¿Qué desea visualizar?
  </h2>
</div>
""", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
<div style="padding:1px 1px 0;">
  <div style="font-size:18px;margin-bottom:2px;">🌱</div>
  <p style="font-size:14px;font-weight:700;color:#1A1A1A;margin:0 0 2px;">Soja</p>
  <p style="font-size:12px;color:#374151;line-height:1.4;margin:0 0 4px;">
    AV1 a AV7 — inicial, enfermedades, floración, arquitectura, caracterización,
    vuelco y cosecha.
  </p>
</div>
""", unsafe_allow_html=True)
        st.page_link("pages/1_Soja.py", label="Abrir Soja", icon="➡️")

    st.write("")

    with st.container(border=True):
        st.markdown("""
<div style="padding:1px 1px 0;">
  <div style="font-size:18px;margin-bottom:2px;">🌽</div>
  <p style="font-size:14px;font-weight:700;color:#1A1A1A;margin:0 0 2px;">Maíz</p>
  <p style="font-size:12px;color:#374151;line-height:1.4;margin:0 0 4px;">
    AV1 a AV4 — inicial, enfermedades, floración/altura y cosecha.
  </p>
</div>
""", unsafe_allow_html=True)
        st.page_link("pages/2_Milho.py", label="Abrir Maíz", icon="➡️")

with col_dir:
    img_path = asset_path("App_development-amico.png")
    if img_path:
        _b64 = base64.b64encode(img_path.read_bytes()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{_b64}" '
            'style="display:block;margin:0.5rem auto 0;max-height:360px;width:auto;max-width:100%;"/>',
            unsafe_allow_html=True,
        )

st.divider()
st.markdown(
    '<div style="text-align:center;">'
    '<p style="font-size:13px;color:#374151;margin:0;">Panel de Fotos y Comentarios · Stine Argentina</p>'
    '<p style="font-size:15px;color:#374151;margin:4px 0 0;">Desarrollado por '
    '<a href="https://www.linkedin.com/in/eng-agro-andre-ferreira/" target="_blank" '
    'style="color:#27AE60;font-weight:700;text-decoration:none;">Andre Ferreira</a></p>'
    '</div>',
    unsafe_allow_html=True,
)
