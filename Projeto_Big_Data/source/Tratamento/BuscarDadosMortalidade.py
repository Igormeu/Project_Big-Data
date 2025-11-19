import os
import requests as rq
import pandas as pd

class BuscarDadosMortalidade:
    def __init__(self, pasta_destino: str = "Recurso/ DataSetBruto"):
        self.pasta_destino = pasta_destino
        os.makedirs(self.pasta_destino, exist_ok=True)

        self.url_2000_2020 = "https://diaad.s3.sa-east-1.amazonaws.com/sim/Mortalidade_Geral_"
        self.url_2021_2021 = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SIM/Mortalidade_Geral_2021.csv"
        self.url_2021_2024 = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SIM/"
        self.extensao = ".csv"

        # Atributo principal que conterá o DataFrame consolidado
        self.df = pd.DataFrame()

    # -----------------------------------------------------------
    # FUNÇÕES INTERNAS (PRIVADAS)
    # -----------------------------------------------------------
    def _montar_url(self, ano: int) -> str:
        """Retorna o link de download correspondente ao ano informado."""
        if ano <= 2020:
            return f"{self.url_2000_2020}{ano}{self.extensao}"
        elif ano == 2021:
            return self.url_2021_2021
        elif ano <= 2025:
            numero_ano = ano - 2000
            return f"{self.url_2021_2024}DO{numero_ano}OPEN{self.extensao}"
        else:
            raise ValueError("Ano fora do intervalo disponível (2000–2025).")

    def _download_arquivo(self, url: str, caminho_local: str):
        """Baixa o arquivo CSV de mortalidade e salva localmente."""
        if os.path.exists(caminho_local):
            print(f"✅ Arquivo '{caminho_local}' já existe. Pulando download.")
            return
        try:
            with rq.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(caminho_local, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"⬇️ Arquivo '{caminho_local}' baixado com sucesso.")
        except rq.exceptions.RequestException as e:
            print(f"❌ Erro ao baixar {url}: {e}")

    # -----------------------------------------------------------
    # MÉTODOS PRINCIPAIS
    # -----------------------------------------------------------
    def baixar_dados(self, anos: list[int]):
        """Baixa os arquivos de mortalidade para os anos informados."""
        for ano in anos:
            url = self._montar_url(ano)
            nome_arquivo = os.path.join(self.pasta_destino, f"Mortalidade_{ano}{self.extensao}")
            self._download_arquivo(url, nome_arquivo)

    def carregar_dataset(self, anos: list[int]):
        """
        Carrega todos os arquivos CSV dos anos informados e guarda no atributo self.df.
        """
        frames = []
        for ano in anos:
            caminho = os.path.join(self.pasta_destino, f"Mortalidade_{ano}{self.extensao}")
            if os.path.exists(caminho):
                try:
                    df = pd.read_csv(caminho, sep=";", encoding="latin1", low_memory=False)
                    df["ANO_OBITO"] = ano
                    frames.append(df)
                    print(f"📂 Dados de {ano} carregados ({len(df)} registros).")
                except Exception as e:
                    print(f"⚠️ Erro ao ler {caminho}: {e}")
            else:
                print(f"⚠️ Arquivo {caminho} não encontrado. Pulei esse ano.")

        if frames:
            self.df = pd.concat(frames, ignore_index=True)
            # Criar coluna de UF a partir do código do município de residência
            if "CODMUNRES" in self.df.columns:
                self.df["CODUF"] = self.df["CODMUNRES"].astype(str).str[:2]
            else:
                print("⚠️ Coluna CODMUNRES não encontrada no dataset de mortalidade.")

            print(f"✅ DataFrame consolidado com {len(self.df)} linhas e {len(self.df.columns)} colunas.")
        else:
            print("❌ Nenhum arquivo válido encontrado. DataFrame vazio.")
            self.df = pd.DataFrame()

    def filtrar_dados(self, ano: int = None, idade_min: int = 460, idade_max: int = None, uf: str = 23):
        """
        Aplica filtros diretamente sobre o atributo self.df.
        Retorna e atualiza o atributo self.df filtrado.
        """
        if self.df.empty:
            print("⚠️ DataFrame vazio. Nenhum filtro aplicado.")
            return self.df

        df_filtrado = self.df.copy()

        # Filtro de ano do óbito
        if ano is not None and "ANO_OBITO" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["ANO_OBITO"] == ano]

        # Filtro de idade (código SIM)
        if "IDADE" in df_filtrado.columns:
            if idade_min is not None:
                df_filtrado = df_filtrado[df_filtrado["IDADE"] >= idade_min]
            if idade_max is not None:
                df_filtrado = df_filtrado[df_filtrado["IDADE"] <= idade_max]

        # Filtro por UF (novo)
        if uf is not None:
            if "CODUF" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["CODUF"] == str(uf).zfill(2)]
            else:
                print("⚠️ Coluna CODUF não encontrada. Filtro ignorado.")

        # Filtro LOCACOR preenchido
        if "LOCACOR" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["LOCACOR"].notna() & (df_filtrado["LOCACOR"] != "")]

        # Atualiza atributo principal
        self.df = df_filtrado.reset_index(drop=True)
        print(f"✅ Filtro aplicado. {len(self.df)} registros restantes.")
        return self.df


    def mostrar_info(self):
        """Exibe informações gerais do DataFrame atual."""
        if self.df.empty:
            print("⚠️ Nenhum dado carregado.")
        else:
            print(f"📊 Linhas: {len(self.df)} | Colunas: {len(self.df.columns)}")
            print(f"🗓️ Anos disponíveis: {sorted(self.df['ANO_OBITO'].unique())}")
            print(f"🧩 Colunas: {list(self.df.columns[:10])}...")

