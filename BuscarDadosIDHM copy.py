# tratar_idhm.py
# Classe para tratar arquivo Excel de IDHM e Renda per capita
# Inclui unpivot completo (pivete), criação de indicador e extração do ano

import pandas as pd
import numpy as np
import re

PATH = "DataIDHM_ce\data.xlsx"

class BuscarDadosIDHM:
    def __init__(self, df_ibge, path_excel = PATH):
    # tratar_idhm.py
        self.path = path_excel
        self.ibge = df_ibge
        self.df_raw = None
        self.df_tratado = None
        self.mapa_nome_para_codigo = None

    def carregar(self):
        """Carrega o Excel."""
        self.df_raw = pd.read_excel(self.path)
        return self.df_raw

    def limpar_nome(self, nome):
        """
        Remove UF e símbolos do nome do município:
        - 'Abaiara (CE)' → 'Abaiara'
        - 'Acopiara (CE)' → 'Acopiara'
        """
        nome = str(nome)
        nome = re.sub(r"\s*\(.*?\)", "", nome)
        return nome.strip()

    def criar_mapa(self):
        """
        Cria dicionário:
        'Abaiara' -> 2300100
        'Acarape' -> 2300150
        usando o DataFrame da classe BuscarDadosIBGE
        """
        df_ibge = self.ibge.copy()

        df_ibge["nome_limpo"] = df_ibge["nome"].apply(lambda x: str(x).strip())

        self.mapa_nome_para_codigo = dict(
            zip(df_ibge["nome_limpo"], df_ibge["id"])
        )

    def substituir_nome_por_codigo(self):
        """Transforma Territorialidades → codigo_municipio."""
        df = self.df_raw.copy()

        df["municipio_limpo"] = df["Territorialidades"].apply(self.limpar_nome)

        df["codigo_municipio"] = df["municipio_limpo"].apply(
            lambda x: self.mapa_nome_para_codigo.get(x)
        )

        df = df[df["codigo_municipio"].notna()].copy()
        df["codigo_municipio"] = df["codigo_municipio"].astype(int)

        self.df_raw = df
        return df

    def unpivotar(self):
        """
        Converte:
        IDHM 2000, IDHM 2010, etc.
        para formato Power BI:
        codigo_municipio | indicador | ano | valor
        """
        df = self.df_raw.copy()

        # todas as colunas que contêm ANO
        col_metricas = [c for c in df.columns if re.search(r"\d{4}", c)]

        df_long = df.melt(
            id_vars=["codigo_municipio"],
            value_vars=col_metricas,
            var_name="coluna_origem",
            value_name="valor"
        )

        df_long["ano"] = df_long["coluna_origem"].str.extract(r"(\d{4})").astype(int)

        df_long["indicador"] = (
            df_long["coluna_origem"]
            .str.replace(r"\s*\d{4}", "", regex=True)
            .str.strip()
        )

        df_long["valor"] = pd.to_numeric(df_long["valor"], errors="coerce")

        self.df_tratado = df_long[["codigo_municipio", "indicador", "ano", "valor"]]
        return self.df_tratado

    def processar(self):
        """Pipeline completo."""
        self.carregar()
        self.criar_mapa()
        self.substituir_nome_por_codigo()
        return self.unpivotar()
