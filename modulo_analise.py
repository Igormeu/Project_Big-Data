import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")   # necessário para Flask
import matplotlib.pyplot as plt
from io import BytesIO

# ============================================================
# Função SIM → idade
# ============================================================

def idade_sim_para_anos(valor):
    try:
        valor = int(valor)
    except:
        return None

    if   400 <= valor <= 499: return valor - 400
    elif 300 <= valor <= 399: return valor - 300
    elif 200 <= valor <= 299: return (valor - 200) / 12
    elif 100 <= valor <= 199: return (valor - 100) / 365
    return None

# ============================================================
# Preparação dos dados consolidados
# ============================================================

def preparar_dados(df_idhm, df_cnes, df_mort):

    # -------------------------
    # IDHM pivotado
    # -------------------------
    df_idhm_wide = df_idhm.pivot_table(
        index="codigo_municipio",
        columns=["indicador", "ano"],
        values="valor"
    )

    df_idhm_wide.columns = [f"{ind}_{ano}" for ind, ano in df_idhm_wide.columns]
    df_idhm_wide = df_idhm_wide.reset_index()

    # -------------------------
    # CNES — padronização da key
    # -------------------------
    df_cnes_base = (
        df_cnes.groupby("codigo_ibge_completo")["qtd_estabelecimentos"]
        .sum()
        .reset_index()
        .rename(columns={
            "codigo_ibge_completo": "codigo_municipio",
            "qtd_estabelecimentos": "cnes_total"
        })
    )

    # -------------------------
    # MORTALIDADE
    # -------------------------
    mun_col = "CODMUNRES"
    df_mort["idade_anos"] = df_mort["IDADE"].apply(idade_sim_para_anos)

    df_mort_base = (
    df_mort.groupby(mun_col)
    .agg(mortes_idosos=("IDADE", "count"))
    .reset_index()
    .rename(columns={mun_col: "codigo_municipio"})
    )

    # -------------------------
    # MERGE FINAL
    # -------------------------
    df_total = (
        df_idhm_wide
            .merge(df_cnes_base, on="codigo_municipio", how="left")
            .merge(df_mort_base, on="codigo_municipio", how="left")
    )

    df_total.fillna(0, inplace=True)
    return df_total

# ============================================================
# Funções de GERAÇÃO DE GRÁFICOS PARA FLASK
# ============================================================

def gerar_scatter(df, x, y, titulo):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df[x], df[y])
    ax.set_title(titulo)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.grid(True)
    return salvar_fig(fig)

def gerar_regressao(df, x, y, titulo):
    m, b = np.polyfit(df[x], df[y], 1)
    y_pred = m * df[x] + b

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df[x], df[y])
    ax.plot(df[x], y_pred, linewidth=2)
    ax.set_title(titulo)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.grid(True)
    return salvar_fig(fig)

def gerar_heatmap(df, cols, titulo):
    corr = df[cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(corr, cmap="viridis")
    fig.colorbar(cax)

    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45)
    ax.set_yticklabels(cols)
    ax.set_title(titulo)

    return salvar_fig(fig)

def gerar_bins(df, x, y, titulo, bins=5):
    df_temp = df.copy()
    df_temp["faixa"] = pd.cut(df_temp[x], bins=bins)

    df_group = df_temp.groupby("faixa")[y].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df_group["faixa"].astype(str), df_group[y])
    ax.set_title(titulo)
    ax.set_xlabel(f"Faixas de {x}")
    ax.set_ylabel(f"Média de {y}")
    ax.grid(axis="y")

    return salvar_fig(fig), df_group

# ============================================================
# Utilitário: retornar imagem para Flask
# ============================================================

def salvar_fig(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf
