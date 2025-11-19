# mapas_ce.py
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ================================================================
# 1. Carregar shapefile
# ================================================================
def carregar_shapefile(path_shapefile):
    print(f"📌 Carregando shapefile: {path_shapefile}")
    mapa = gpd.read_file(path_shapefile)

    # corrigir problemas de geometria
    mapa = mapa[mapa.geometry.notna()].copy()
    mapa = mapa[~mapa.geometry.is_empty].copy()

    print(f"✔ Shapefile carregado com {len(mapa)} municípios.")
    return mapa


# ================================================================
# 2. Detectar automaticamente coluna do IBGE no shapefile
# ================================================================
def detectar_coluna_codigo(mapa):
    possiveis = ["CD_MUN", "CD_GEOCMU", "codigo_ibge", "cod_ibge", "CD_MUN", "GEOCODIGO"]
    for col in mapa.columns:
        if col.upper() in [x.upper() for x in possiveis]:
            return col

    # fallback: procurar coluna de 7 dígitos
    for col in mapa.columns:
        if mapa[col].astype(str).str.match(r"^\d{7}$").sum() > 200:
            return col

    raise Exception("❌ Nenhuma coluna válida de código IBGE encontrada no shapefile.")


# ================================================================
# 3. Filtrar somente municípios do Ceará (CE)
# ================================================================
def preparar_mapa_ce(mapa, df_total):
    print("📌 Preparando mapa do Ceará...")

    # 1. Detectar coluna do IBGE no shapefile automaticamente
    col_cod = detectar_coluna_codigo(mapa)
    print(f"✔ Coluna IBGE detectada no shapefile: {col_cod}")

    # garantir formato numérico
    mapa[col_cod] = mapa[col_cod].astype(str).str[:7]
    df_total["codigo_municipio"] = df_total["codigo_municipio"].astype(str).str[:7]

    # filtrar só municípios que estão no dataset
    mapa_ce = mapa.merge(
        df_total,
        left_on=col_cod,
        right_on="codigo_municipio",
        how="inner"
    )

    print(f"✔ Mapa CE após merge: {mapa_ce.shape[0]} municípios")

    # corrigir geometrias inválidas novamente
    mapa_ce = mapa_ce[mapa_ce.geometry.notna()]
    mapa_ce = mapa_ce[~mapa_ce.geometry.is_empty]

    return mapa_ce


# ================================================================
# 4. Plotar mapa de mortalidade
# ================================================================
def mapa_mortalidade(mapa_ce, coluna="mortes_idosos", salvar_em=None):

    if mapa_ce.shape[0] == 0:
        raise ValueError("❌ mapa_ce está vazio! Nenhum município encontrado.")

    if coluna not in mapa_ce.columns:
        raise ValueError(f"❌ Coluna '{coluna}' não existe no mapa_ce.")

    fig, ax = plt.subplots(figsize=(12, 10))

    mapa_ce.plot(
        column=coluna,
        ax=ax,
        cmap="Reds",
        legend=True,
        linewidth=0.3,
        edgecolor="black",
    )

    ax.set_title(f"Mortalidade de Idosos — Ceará", fontsize=16)

    # EVITAR O ERRO DO ASPECT
    ax.set_aspect("equal")

    if salvar_em:
        fig.savefig(salvar_em, dpi=300, bbox_inches="tight")
        print(f"💾 Mapa salvo em: {salvar_em}")

    return fig
