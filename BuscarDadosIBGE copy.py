import requests
import pandas as pd

class BuscarDadosIBGE:
    """
    Classe para consultar e manipular dados de municípios via API IBGE.
    Atributos:
        df (pd.DataFrame): tabela com os dados dos municípios.
    """

    URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

    def __init__(self, auto_load=True):
        self.df = pd.DataFrame()  # atributo DataFrame
        if auto_load:
            self.atualizar_dados()

    def atualizar_dados(self):
        resp = requests.get(self.URL)
        resp.raise_for_status()
        data = resp.json()
        self.df = pd.json_normalize(data)
        return True

    def filtrar_por_estado(self, sigla_uf):
        """Retorna um novo DataFrame com os municípios da UF informada (ex: 'SP', 'BA')."""
        sigla_uf = sigla_uf.upper()
        filtro = self.df[self.df["microrregiao.mesorregiao.UF.sigla"] == sigla_uf]
        return filtro.reset_index(drop=True)

    def listar_estados(self):
        """Retorna lista única de siglas de estados disponíveis."""
        return sorted(self.df["microrregiao.mesorregiao.UF.sigla"].unique())

    def salvar(self, caminho="municipios_ibge.xlsx"):
        """Salva o DataFrame atual em Excel."""
        self.df.to_excel(caminho, index=False)
        print(f"💾 Dados salvos em: {caminho}")

    def __repr__(self):
        return f"<MunicipiosIBGE: {len(self.df)} municípios carregados>"