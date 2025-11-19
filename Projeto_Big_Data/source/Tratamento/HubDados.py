# data_hub_ce.py

from source.Tratamento.BuscarDadosIBGE import BuscarDadosIBGE
from source.Tratamento.BuscarDadosEstabelecimentos import BuscarDadosEstabelecimentos
from source.Tratamento.BuscarDadosIDHM import BuscarDadosIDHM
from source.Tratamento.BuscarDadosMortalidade import BuscarDadosMortalidade

class DataHubCE:
    """
    Classe agregadora que orquestra o carregamento e tratamento
    dos dados do Ceará: IBGE, CNES, IDHM e Mortalidade.
    """

    def __init__(self):
        # Instâncias das classes base
        print("🔄 Carregando dados do IBGE...")
        self.ibge = BuscarDadosIBGE(auto_load=True)

        print("🔄 Preparando módulos...")
        # self.cnes = BuscarDadosEstabelecimentos(self.df_ibge)
        # self.idhm = BuscarDadosIDHM(self.df_ibge)
        self.mortalidade = BuscarDadosMortalidade()

        # DataFrames processados
        self.df_ibge = None
        self.df_cnes = None
        self.df_idhm = None
        self.df_mortalidade = None

    # ============================================================
    # MÉTODOS PRINCIPAIS
    # ============================================================

    def carregar_ibge(self):
        print("📌 Processando dados do IBGE...")
        self.df_ibge = self.ibge.filtrar_por_estado("CE")
        return self.df_ibge

    def carregar_cnes(self):
        print("📌 Processando dados CNES...")
        self.cnes = BuscarDadosEstabelecimentos(df_ibge=self.df_ibge)
        self.df_cnes = self.cnes.processar()
        return self.df_cnes

    def carregar_idhm(self):
        print("📌 Processando dados do IDHM...")
        self.idhm = BuscarDadosIDHM(df_ibge=self.df_ibge)
        self.df_idhm = self.idhm.processar()
        return self.df_idhm

    def carregar_mortalidade(self, anos=list([2000,2010])):
        print(f"📌 Baixando e processando mortalidade: anos {anos}")
        self.mortalidade.baixar_dados(anos)
        self.mortalidade.carregar_dataset(anos)
        self.mortalidade.filtrar_dados(idade_min=460)
        self.df_mortalidade = self.mortalidade.df
        return self.df_mortalidade

    def atualizar_dados(self, atualizar_cnes=True, atualizar_idhm=True, atualizar_mortalidade=True,atualizar_ibge=True):
        global progresso, log_texto, atualizando
        atualizando = True
        progresso = 0
        log_texto = "Iniciando atualização...\n"

        try:
            if atualizar_ibge:
                self.escrever_log("Atualizando IBGE...")
                self.carregar_ibge()
                self.incrementar_progresso(10)

            if atualizar_cnes:
                self.escrever_log("Atualizando CNES...")
                self.carregar_cnes()
            self.incrementar_progresso(25)

            if atualizar_idhm:
                self.escrever_log("Atualizando IDHM...")
                self.carregar_idhm()
            self.incrementar_progresso(25)

            if atualizar_mortalidade:
                self.escrever_log("Atualizando Mortalidade...")
                self.carregar_mortalidade()
            self.incrementar_progresso(40)

            self.escrever_log("Finalizado!")
            atualizando = False

        except Exception as e:
            self.escrever_log(f"Erro: {e}")
            atualizando = False
            raise e

    def escrever_log(self, texto):
        global log_texto
        log_texto += texto + "\n"

    def incrementar_progresso(self, valor):
        global progresso
        progresso = min(100, progresso + valor)

    # ============================================================
    # PIPELINE COMPLETO
    # ============================================================

    def carregar_tudo(self):
        """
        Executa toda a pipeline de dados.
        """
        print("\n🚀 Iniciando pipeline completa...\n")

        self.carregar_ibge()
        self.carregar_cnes()
        self.carregar_idhm()
        self.carregar_mortalidade()

        # print(self.df_mortalidade.describe())
        # print(self.df_mortalidade.info())
        
        print("\n✅ Pipeline concluída!\n")
        return {
            "ibge": self.df_ibge,
            "cnes": self.df_cnes,
            "idhm": self.df_idhm,
            "mortalidade": self.df_mortalidade,
        }
