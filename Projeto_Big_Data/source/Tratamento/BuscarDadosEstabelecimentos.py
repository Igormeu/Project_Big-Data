# tratar_cnes.py
# Classe para tratar dados CNES baixados manualmente no TABNET
# Replicando arquitetura do módulo IDHM (funciona igual)

import pandas as pd
import numpy as np
import re
import unicodedata

PATH = "Recurso/dados_cnes_ce/QuantidadeCNES.csv"

def normalizar_nome(nome):
    """Remove acentos, deixa minúsculo e remove múltiplos espaços."""
    nome = str(nome).strip().lower()
    nome = unicodedata.normalize("NFD", nome)
    nome = nome.encode("ascii", "ignore").decode("utf-8")
    nome = re.sub(r"\s+", " ", nome)
    return nome

class BuscarDadosEstabelecimentos:
    def __init__(self, df_ibge, path_csv = PATH):
        self.path = path_csv
        self.ibge = df_ibge             # DataFrame do IBGE
        self.df_raw = None
        self.df_tratado = None
        self.mapa_nome_para_codigo = None

    # --------------------------------------------
    def carregar(self):
        """Carrega CSV original do TABNET."""
        self.df_raw = pd.read_csv(
            self.path,
            sep=";",
            encoding="latin1",
            quotechar='"'
        )

        # Normaliza colunas
        self.df_raw.columns = self.df_raw.columns.str.strip()
        return self.df_raw

    # --------------------------------------------
    def separar_codigo_nome(self):
        """Separa '230010 ABAIARA' em código e nome limpo."""
        df = self.df_raw.copy()

        df["codigo_tabnet"] = df["Municipio"].str.extract(r"^(\d+)")
        df["municipio"] = df["Municipio"].str.replace(r"^\d+\s*", "", regex=True)

        df = df[df["codigo_tabnet"].notna()]
        df["codigo_tabnet"] = df["codigo_tabnet"].astype(int)

        df["municipio_limpo"] = df["municipio"].apply(normalizar_nome)

        self.df_raw = df
        return df

    # --------------------------------------------
    def criar_mapa(self):
        """Cria dicionário: 'abaiara' → 2300100."""
        df_ibge = self.ibge.copy()

        df_ibge["nome_limpo"] = df_ibge["nome"].apply(normalizar_nome)

        self.mapa_nome_para_codigo = dict(
            zip(df_ibge["nome_limpo"], df_ibge["id"])
        )

    # --------------------------------------------
    def substituir_nome_por_codigo(self):
        """Troca nome pelo código IBGE correto."""
        df = self.df_raw.copy()

        df["codigo_ibge_completo"] = df["municipio_limpo"].apply(
            lambda x: self.mapa_nome_para_codigo.get(x)
        )

        df = df[df["codigo_ibge_completo"].notna()].copy()
        df["codigo_ibge_completo"] = df["codigo_ibge_completo"].astype(int)

        self.df_raw = df
        return df

    # --------------------------------------------
    def unpivotar(self):
        """Transforma 2005/Dez ... 2024/Dez em formato Power BI."""
        df = self.df_raw.copy()

        # Capturar todas as colunas de ano
        col_anos = [c for c in df.columns if re.match(r"^\d{4}/Dez$", c)]

        df_long = df.melt(
            id_vars=["codigo_ibge_completo"],
            value_vars=col_anos,
            var_name="coluna_origem",
            value_name="qtd_estabelecimentos"
        )

        df_long["ano"] = df_long["coluna_origem"].str.extract(r"(\d{4})").astype(int)

        df_long["qtd_estabelecimentos"] = pd.to_numeric(
            df_long["qtd_estabelecimentos"], errors="coerce"
        ).fillna(0).astype(int)

        self.df_tratado = df_long[[
            "codigo_ibge_completo",
            "ano",
            "qtd_estabelecimentos"
        ]]

        return self.df_tratado

    # --------------------------------------------
    def processar(self):
        """Pipeline igual ao IDHM."""
        self.carregar()
        self.separar_codigo_nome()
        self.criar_mapa()
        self.substituir_nome_por_codigo()
        return self.unpivotar()
