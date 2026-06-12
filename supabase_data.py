"""
supabase_data.py
Carregamento das fotos e comentarios de campo a partir do Supabase.
Funciona para as duas culturas: Soja e Milho.

Estrutura confirmada da base argentina:
  avXDetalheTratamento{Cultura} : uuid, nota, photoUrl, dataCriacao,
                                  tratamentoRef, fazendaRef
  avXTratamento{Cultura}        : uuid, nome (= cultivar/hibrido), tipoTeste,
                                  populacao, avaliacaoRef, idBaseRef
  fazenda                       : uuid, nomeFazenda, nomeProdutor, safra, regional
  avaliacao                     : uuid, faseFenologica, tipoAvaliacao
"""

import warnings

import numpy as np
import pandas as pd
import streamlit as st
from supabase import create_client

warnings.filterwarnings("ignore")


# ── Conexao Supabase ──────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    """
    Cria o cliente Supabase. URL e KEY vem de .streamlit/secrets.toml —
    e o unico lugar a editar para apontar para outra base.
    """
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


# ── Extracao com paginacao ────────────────────────────────────────────────────
def _extrair(sb, nome: str, page_size: int = 1000) -> pd.DataFrame:
    """
    Extrai uma tabela inteira do Supabase, em lotes de 1000 linhas
    (limite por requisicao). Tabela inexistente -> DataFrame vazio.
    """
    linhas, inicio = [], 0
    while True:
        try:
            resp = (
                sb.table(nome)
                .select("*")
                .range(inicio, inicio + page_size - 1)
                .execute()
            )
        except Exception:
            break
        lote = resp.data or []
        linhas.extend(lote)
        if len(lote) < page_size:
            break
        inicio += page_size
    return pd.DataFrame(linhas)


def _limpar_texto(serie: pd.Series) -> pd.Series:
    """Normaliza uma coluna de texto: vazios e 'null'/'None' viram NaN."""
    return (
        serie.astype(str).str.strip()
        .replace({"": np.nan, "null": np.nan, "None": np.nan,
                  "nan": np.nan, "NaN": np.nan})
    )


# ── Carregamento principal ────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_fotos_comentarios(cultura: str) -> dict:
    """
    cultura: "Soja" ou "Milho".

    Retorna {"av1": df, "av2": df, ..., "av7": df}.
    Avaliacoes sem tabela de detalhe ou sem dados retornam DataFrame vazio.

    Cada DataFrame traz as colunas usadas pela pagina:
        photoUrl, nota, dataCriacao,
        cultivar (nome do hibrido/cultivar), nomeFazenda, nomeProdutor,
        safra, regional, tipoTeste, tipoAvaliacao
    """
    sb = get_supabase()

    # ── Tabelas de apoio (uma vez so) ────────────────────────────────────────
    df_fazenda   = _extrair(sb, "fazenda")
    df_avaliacao = _extrair(sb, "avaliacao")

    # Contexto da fazenda: nome, produtor, safra, regional
    ctx_fazenda = pd.DataFrame(
        columns=["fazendaRef", "nomeFazenda", "nomeProdutor", "safra", "regional"]
    )
    if not df_fazenda.empty and "uuid" in df_fazenda.columns:
        f = df_fazenda.copy()
        for c in ["nomeFazenda", "nomeProdutor", "safra", "regional"]:
            if c not in f.columns:
                f[c] = np.nan
        f["nomeFazenda"]  = f["nomeFazenda"].astype(str).str.strip()
        f["nomeProdutor"] = f["nomeProdutor"].astype(str).str.strip()
        ctx_fazenda = f[["uuid", "nomeFazenda", "nomeProdutor",
                         "safra", "regional"]].rename(columns={"uuid": "fazendaRef"})

    # Contexto da avaliacao: fase fenologica e tipo de avaliacao
    ctx_aval = pd.DataFrame(columns=["avaliacaoRef", "faseFenologica", "tipoAvaliacao"])
    if not df_avaliacao.empty and "uuid" in df_avaliacao.columns:
        a = df_avaliacao.copy()
        for c in ["faseFenologica", "tipoAvaliacao"]:
            if c not in a.columns:
                a[c] = np.nan
        a["faseFenologica"] = _limpar_texto(a["faseFenologica"])
        a["tipoAvaliacao"]  = _limpar_texto(a["tipoAvaliacao"])
        ctx_aval = a[["uuid", "faseFenologica", "tipoAvaliacao"]].rename(
            columns={"uuid": "avaliacaoRef"}
        )

    # ── Detalhe enriquecido por avaliacao ────────────────────────────────────
    resultado = {}
    for i in range(1, 8):
        av = f"av{i}"
        df_det  = _extrair(sb, f"{av}DetalheTratamento{cultura}")
        df_trat = _extrair(sb, f"{av}Tratamento{cultura}")

        if df_det.empty:
            resultado[av] = pd.DataFrame()
            continue

        # fotoBase64 pode ser enorme — descartar sempre
        df_det = df_det.drop(
            columns=[c for c in ["fotoBase64", "dataSync", "acao", "firebase"]
                     if c in df_det.columns]
        )

        # Data de criacao: timestamp Unix em segundos
        if "dataCriacao" in df_det.columns:
            df_det["dataCriacao"] = pd.to_datetime(
                df_det["dataCriacao"], unit="s", errors="coerce"
            )

        # Foto e comentario
        for col in ["nota", "photoUrl"]:
            if col in df_det.columns:
                df_det[col] = _limpar_texto(df_det[col])

        # Contexto do tratamento (cultivar/hibrido vem do campo 'nome')
        if not df_trat.empty and "uuid" in df_trat.columns:
            cols_trat = [c for c in ["uuid", "nome", "tipoTeste",
                                     "populacao", "avaliacaoRef"]
                         if c in df_trat.columns]
            lookup = df_trat[cols_trat].rename(columns={"uuid": "tratamentoRef"})
            df_det = df_det.merge(lookup, on="tratamentoRef", how="left")

        df_det["cultivar"] = (
            _limpar_texto(df_det["nome"]) if "nome" in df_det.columns else np.nan
        )

        # Contexto da fazenda
        if "fazendaRef" in df_det.columns:
            df_det = df_det.merge(ctx_fazenda, on="fazendaRef", how="left")

        # Contexto da avaliacao
        if "avaliacaoRef" in df_det.columns:
            df_det = df_det.merge(ctx_aval, on="avaliacaoRef", how="left")

        resultado[av] = df_det.reset_index(drop=True)

    return resultado
