from flask import Flask
from source.Tratamento.HubDados import DataHubCE
from source.modulo_analise import (
    preparar_dados
)
import threading
import time

hub = DataHubCE()

atualizando = False
progresso = 0
log_texto = ""

dados_carregados = False
df_total = None

def atualizar_background():
    """Executa atualização completa em thread"""
    global atualizando, progresso, log_texto

    etapas = [
        ("IBGE", lambda: hub.atualizar_dados(atualizar_cnes=False, atualizar_idhm=False, atualizar_mortalidade=False)),
        ("CNES", lambda: hub.atualizar_dados(atualizar_ibge=True, atualizar_idhm=False, atualizar_mortalidade=False)),
        ("IDHM", lambda: hub.atualizar_dados(atualizar_ibge=True, atualizar_cnes=False, atualizar_mortalidade=False)),
        ("Mortalidade", lambda: hub.atualizar_dados(atualizar_ibge=False, atualizar_cnes=False, atualizar_idhm=False)),
    ]

    atualizando = True
    progresso = 0
    log_texto = "Iniciando atualização...\n"

    total = len(etapas)

    for i, (nome, func) in enumerate(etapas, start=1):
        log_texto += f"\n🔄 Atualizando {nome}...\n"
        progresso = int((i - 1) / total * 100)

        func()

        progresso = int(i / total * 100)
        log_texto += f"✔️ {nome} concluído!\n"

        time.sleep(1)

    log_texto += "\n🎉 Atualização finalizada!"
    atualizando = False


def loop_auto_update():
    """Atualiza a cada 5 min automaticamente"""
    while True:
        time.sleep(300)
        if not atualizando:
            threading.Thread(target=atualizar_background).start()

def create_app():
    from routes import bp_main, bp_graficos   # evita circular import

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "CEARÁ-DADOS-2025"

    # Carregar rotas (Blueprints)
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_graficos)

    # Iniciar auto-update
    threading.Thread(target=loop_auto_update, daemon=True).start()

    return app
