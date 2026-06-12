"""
pagina_fotos.py
Lógica compartida de la página de Fotos y Comentarios.

Las páginas pages/1_Soja.py y pages/2_Milho.py solo llaman render(cultura),
para que exista UNA única copia del código de la galería, filtros y tabla.

NOTA: el argumento `cultura` ("Soja"/"Milho") se usa para armar el nombre de
las tablas del Supabase (avXDetalheTratamento<cultura>), por eso NO se traduce.
El rótulo visible se traduce vía ROTULO_CULTURA (Milho -> Maíz).
"""

import streamlit.components.v1 as components
import pandas as pd
import streamlit as st

from theme import aplicar_tema, page_header, secao_titulo, bandeira_ar_html
from supabase_data import carregar_fotos_comentarios
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


# ── Rótulo visible del cultivo (el valor interno sigue siendo Soja/Milho) ─────
ROTULO_CULTURA = {"Soja": "Soja", "Milho": "Maíz"}

# ── Rótulos de las evaluaciones por cultivo ──────────────────────────────────
# Las evaluaciones sin datos no aparecen; estos son solo los rótulos amigables.
AV_NOMES = {
    "Milho": {
        "av1": "AV1 · Evaluación Inicial",
        "av2": "AV2 · Enfermedades",
        "av3": "AV3 · Floración y Altura",
        "av4": "AV4 · Cosecha",
    },
    "Soja": {
        "av1": "AV1 · Evaluación Inicial",
        "av2": "AV2 · Enfermedades",
        "av3": "AV3 · Floración",
        "av4": "AV4 · Arquitectura de Planta",
        "av5": "AV5 · Caracterización",
        "av6": "AV6 · Vuelco",
        "av7": "AV7 · Cosecha",
    },
}

AG_CSS = {
    ".ag-header":            {"background-color": "#4A4A4A !important"},
    ".ag-header-row":        {"background-color": "#4A4A4A !important"},
    ".ag-header-cell":       {"background-color": "#4A4A4A !important"},
    ".ag-header-cell-label": {"color": "#FFFFFF !important", "font-weight": "700"},
    ".ag-header-cell-text":  {"color": "#FFFFFF !important", "font-size": "13px !important",
                              "font-weight": "700 !important"},
    ".ag-icon":              {"color": "#FFFFFF !important", "opacity": "1 !important"},
    ".ag-row":               {"font-size": "13px !important"},
}


def _tabela(df: pd.DataFrame, altura: int = 420):
    """Renderiza un DataFrame como AgGrid con el encabezado oscuro del tema."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        resizable=True, sortable=True, filter=True,
        wrapText=True, autoHeight=True,
        cellStyle={"fontSize": "13px", "fontFamily": "Helvetica Neue, sans-serif"},
    )
    gb.configure_grid_options(headerHeight=36, rowHeight=32, domLayout="normal")
    AgGrid(
        df,
        gridOptions=gb.build(),
        height=altura,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        custom_css=AG_CSS,
        theme="streamlit",
        use_container_width=True,
    )


def _galeria(df_fotos: pd.DataFrame):
    """Arma la galería de fotos en grid, con modal de ampliación."""
    cards = ""
    for _, rec in df_fotos.iterrows():
        cultivar = str(rec.get("cultivar") or "—").replace("'", "&#39;")
        fazenda  = str(rec.get("nomeFazenda") or "—").replace("'", "&#39;")
        produtor = str(rec.get("nomeProdutor") or "").replace("'", "&#39;")
        data_val = rec.get("dataCriacao")
        data_str = (pd.to_datetime(data_val, errors="coerce").strftime("%d/%m/%Y")
                    if pd.notna(data_val) else "—")
        nota_val = rec.get("nota")
        nota_str = (str(nota_val).strip()
                    if pd.notna(nota_val) and str(nota_val).strip() not in ("", "nan")
                    else "")
        foto_url = str(rec.get("photoUrl") or "").replace("'", "%27")
        if not foto_url:
            continue

        sub = f"{fazenda}" + (f" · {produtor}" if produtor and produtor != fazenda else "")
        coment_list = rec.get("_comentarios") or []
        if coment_list:
            itens = "".join(f'<div class="foto-coment-item">{c}</div>' for c in coment_list)
            comentario = (
                '<div class="foto-comentario">'
                '<span class="foto-coment-label">Comentarios</span>'
                f'{itens}</div>'
            )
        else:
            comentario = ""
        cards += f"""
<div class="foto-card">
  <img src="{foto_url}" alt="{cultivar}"
       onclick="abrir('{foto_url}','{cultivar}','{sub}','{data_str}')"
       onerror="this.style.display='none'"/>
  <div class="foto-info">
    <div class="foto-cultivar">{cultivar}</div>
    <div class="foto-fazenda">{sub}</div>
    <div class="foto-data">{data_str}</div>
  </div>
  {comentario}
</div>"""

    html = f"""
<!DOCTYPE html><html><head><style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Helvetica Neue',Arial,sans-serif;}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:4px;}}
.foto-card{{border:1px solid #E5E7EB;border-radius:10px;overflow:hidden;background:#fff;
  transition:transform .15s,box-shadow .15s;}}
.foto-card:hover{{transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.12);}}
.foto-card img{{width:100%;height:360px;object-fit:cover;display:block;background:#F3F4F6;cursor:pointer;}}
.foto-info{{padding:8px 10px;}}
.foto-cultivar{{font-weight:700;font-size:13px;color:#111827;margin-bottom:2px;}}
.foto-fazenda{{font-size:12px;color:#6B7280;margin-bottom:2px;}}
.foto-data{{font-size:11px;color:#9CA3AF;}}
.foto-comentario{{background:#F3F4F6;border-top:1px solid #E5E7EB;border-left:3px solid #27AE60;
  padding:8px 12px;font-size:12px;color:#374151;line-height:1.5;}}
.foto-coment-label{{display:block;font-size:9px;font-weight:700;color:#1E8449;
  text-transform:uppercase;letter-spacing:0.05em;margin-bottom:3px;}}
.foto-coment-item{{margin-bottom:4px;}}
.foto-coment-item:last-child{{margin-bottom:0;}}
.ov{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;
  align-items:center;justify-content:center;flex-direction:column;}}
.ov.on{{display:flex;}}
.ov img{{max-width:90vw;max-height:78vh;object-fit:contain;border-radius:8px;}}
.ov .info{{color:#fff;text-align:center;margin-top:12px;}}
.ov .ti{{font-size:18px;font-weight:700;}}
.ov .su{{font-size:13px;color:#D1D5DB;margin-top:4px;}}
.ov .x{{position:fixed;top:18px;right:26px;font-size:30px;color:#fff;cursor:pointer;opacity:.85;}}
.ov .dl{{display:inline-block;margin-top:12px;padding:8px 20px;background:#27AE60;color:#fff;
  border-radius:6px;font-size:13px;font-weight:600;text-decoration:none;}}
</style></head><body>
<div class="grid">{cards}</div>
<div class="ov" id="ov" onclick="if(event.target.id==='ov')this.classList.remove('on')">
  <span class="x" onclick="document.getElementById('ov').classList.remove('on')">✕</span>
  <img id="ov-img" src="" alt=""/>
  <div class="info">
    <div class="ti" id="ov-ti"></div>
    <div class="su" id="ov-su"></div>
    <a class="dl" id="ov-dl" href="" download="" target="_blank">⬇️ Descargar foto</a>
  </div>
</div>
<script>
function abrir(url,ti,su,data){{
  document.getElementById('ov-img').src=url;
  document.getElementById('ov-ti').textContent=ti;
  document.getElementById('ov-su').textContent=su+' · '+data;
  var dl=document.getElementById('ov-dl');
  dl.href=url;
  dl.download=(ti+'_'+data).replace(/[^a-zA-Z0-9]/g,'_')+'.jpg';
  document.getElementById('ov').classList.add('on');
}}
document.addEventListener('keydown',function(e){{
  if(e.key==='Escape')document.getElementById('ov').classList.remove('on');
}});
</script>
</body></html>"""

    altura = max(300, ((len(df_fotos) + 3) // 4) * 480 + 40)
    components.html(html, height=altura, scrolling=True)


def render(cultura: str, icone: str = "📷", imagem: str = ""):
    """
    Renderiza la página completa de Fotos y Comentarios para un cultivo.
    cultura: "Soja" o "Milho" (valor interno usado en el Supabase).
    """
    rotulo = ROTULO_CULTURA.get(cultura, cultura)

    st.set_page_config(
        page_title=f"Fotos y Comentarios · {rotulo}",
        page_icon=icone,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    aplicar_tema()
    # Ilustración del header en tamaño consistente entre páginas.
    st.markdown("<style>.jaum-header > img { height: 100px !important; }</style>", unsafe_allow_html=True)

    page_header(
        f"Fotos y Comentarios · {rotulo}",
        "Registros fotográficos y observaciones de campo · Argentina",
        imagem=imagem,
        bandeira=bandeira_ar_html(),
    )

    with st.spinner(f"Cargando registros de {rotulo}..."):
        det = carregar_fotos_comentarios(cultura)

    # Evaluaciones que efectivamente tienen registros
    avs_com_dados = [av for av in sorted(det) if not det[av].empty]

    if not avs_com_dados:
        st.info(
            f"ℹ️ El cultivo **{rotulo}** todavía no posee fotos y comentarios "
            f"registrados en la base. Apenas haya registros, esta página "
            f"los mostrará automáticamente."
        )
        return

    # Junta todo para extraer las opciones de filtro
    df_all = pd.concat(
        [det[av].assign(_av=av) for av in avs_com_dados],
        ignore_index=True,
    )

    def _opcoes(col):
        if col not in df_all.columns:
            return []
        return sorted(df_all[col].dropna().astype(str).unique().tolist())

    # ── Sidebar — filtros ────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f'<p style="font-size:11px;font-weight:600;color:#6B7280;'
            f'text-transform:uppercase;letter-spacing:0.05em;padding:0.3rem;">'
            f'Filtros · {rotulo}</p>',
            unsafe_allow_html=True,
        )
        safras_sel   = st.multiselect("Campaña",          _opcoes("safra"))
        fazendas_sel = st.multiselect("Campo",            _opcoes("nomeFazenda"))
        cultivar_sel = st.multiselect("Cultivar/Híbrido", _opcoes("cultivar"))
        tipos_sel    = st.multiselect("Tipo de Ensayo",   _opcoes("tipoTeste"))

        st.markdown("---")
        so_foto = st.checkbox("Solo registros con foto",       value=False)
        so_nota = st.checkbox("Solo registros con comentario", value=False)

    def _aplicar_filtros(df):
        d = df.copy()
        if safras_sel and "safra" in d.columns:
            d = d[d["safra"].astype(str).isin(safras_sel)]
        if fazendas_sel and "nomeFazenda" in d.columns:
            d = d[d["nomeFazenda"].astype(str).isin(fazendas_sel)]
        if cultivar_sel and "cultivar" in d.columns:
            d = d[d["cultivar"].astype(str).isin(cultivar_sel)]
        if tipos_sel and "tipoTeste" in d.columns:
            d = d[d["tipoTeste"].astype(str).isin(tipos_sel)]
        if so_foto and "photoUrl" in d.columns:
            d = d[d["photoUrl"].notna()]
        if so_nota and "nota" in d.columns:
            d = d[d["nota"].notna()]
        return d

    # Resumen general
    df_filtrado_total = _aplicar_filtros(df_all)
    n_fotos_g = df_filtrado_total["photoUrl"].notna().sum() if "photoUrl" in df_filtrado_total else 0
    n_notas_g = df_filtrado_total["nota"].notna().sum()     if "nota"     in df_filtrado_total else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Registros", f"{len(df_filtrado_total):,}".replace(",", "."))
    c2.metric("Con foto",  f"{int(n_fotos_g):,}".replace(",", "."))
    c3.metric("Con comentario", f"{int(n_notas_g):,}".replace(",", "."))

    # ── Pestañas por evaluación ──────────────────────────────────────────────
    rotulos = AV_NOMES.get(cultura, {})
    tab_labels = [rotulos.get(av, av.upper()) for av in avs_com_dados]
    tabs = st.tabs(tab_labels)

    for tab, av in zip(tabs, avs_com_dados):
        with tab:
            df_av = _aplicar_filtros(det[av])

            if df_av.empty:
                st.info("Ningún registro para los filtros seleccionados en esta evaluación.")
                continue

            df_fotos = (df_av[df_av["photoUrl"].notna()]
                        if "photoUrl" in df_av.columns else df_av.iloc[0:0])
            df_notas = (df_av[df_av["nota"].notna()]
                        if "nota" in df_av.columns else df_av.iloc[0:0])

            # Asociar a cada foto los comentarios del mismo tratamiento
            # (mismo material/evaluación/campo). Foto y comentario suelen estar
            # en registros distintos, por eso se agrupa por tratamentoRef.
            if not df_fotos.empty:
                df_fotos = df_fotos.copy()
                chave_cols = (["tratamentoRef"] if "tratamentoRef" in df_av.columns
                              else [c for c in ["cultivar", "nomeFazenda"] if c in df_av.columns])
                mapa_notas = {}
                if chave_cols and "nota" in df_av.columns:
                    for _, r in df_av[df_av["nota"].notna()].iterrows():
                        k = tuple(r.get(c) for c in chave_cols)
                        nv = str(r.get("nota")).strip()
                        if nv and nv.lower() != "nan":
                            mapa_notas.setdefault(k, [])
                            if nv not in mapa_notas[k]:
                                mapa_notas[k].append(nv)

                def _coments(row):
                    out = []
                    nv = row.get("nota")
                    if pd.notna(nv) and str(nv).strip() and str(nv).strip().lower() != "nan":
                        out.append(str(nv).strip())
                    if chave_cols:
                        for n in mapa_notas.get(tuple(row.get(c) for c in chave_cols), []):
                            if n not in out:
                                out.append(n)
                    return out

                df_fotos["_comentarios"] = df_fotos.apply(_coments, axis=1)

            st.caption(
                f"ℹ️ {len(df_av)} registros · {len(df_fotos)} con foto · "
                f"{len(df_notas)} con comentario"
            )

            # Galería
            secao_titulo("Galería", "Fotos de campo", "")
            if df_fotos.empty:
                st.info("No hay fotos disponibles para los filtros activos.")
            else:
                _galeria(df_fotos)

            # Comentarios
            secao_titulo("Comentarios", "Observaciones de los técnicos", "")
            if df_notas.empty:
                st.info("No hay comentarios disponibles para los filtros activos.")
            else:
                col_map = {
                    "safra":         "Campaña",
                    "nomeFazenda":   "Campo",
                    "nomeProdutor":  "Productor",
                    "cultivar":      "Cultivar/Híbrido",
                    "tipoTeste":     "Tipo de Ensayo",
                    "tipoAvaliacao": "Evaluación",
                    "dataCriacao":   "Fecha",
                    "nota":          "Comentario",
                }
                cols = [c for c in col_map if c in df_notas.columns]
                df_show = df_notas[cols].rename(columns=col_map).copy()
                if "Fecha" in df_show.columns:
                    df_show["Fecha"] = (
                        pd.to_datetime(df_show["Fecha"], errors="coerce")
                        .dt.strftime("%d/%m/%Y").fillna("")
                    )
                _tabela(df_show, altura=min(520, 60 + 40 * len(df_show)))

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
