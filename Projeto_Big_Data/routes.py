# routes.py
from flask import Blueprint, render_template, request, send_file, jsonify
# from config import (
#     hub, df_total, atualizando, progresso, log_texto,
#     atualizar_background
# )
from source.modulo_analise import (
    gerar_scatter, gerar_regressao,
    gerar_heatmap, gerar_bins
)
from source.Tratamento.HubDados import DataHubCE
from source.modulo_analise import preparar_dados


bp_main = Blueprint("main", __name__)

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
    df_total = preparar_dados(hub.df_idhm, hub.df_cnes, hub.df_mortalidade)

def loop_auto_update():
    """Atualiza a cada 5 min automaticamente"""
    while True:
        time.sleep(300)
        if not atualizando:
            threading.Thread(target=atualizar_background).start()

@bp_main.before_request
def carregar_dados ():
    global df_total, dados_carregados
    if not dados_carregados:
        hub = DataHubCE()
        dados = hub.carregar_tudo()
        df_total = preparar_dados(dados["idhm"], dados["cnes"], dados["mortalidade"])
        dados_carregados = True

@bp_main.route("/")
def home():

    return render_template("index.html", titulo="Dashboard Cearense")


@bp_main.route("/atualizar", methods=["POST"])
def atualizar():
    if not atualizando:
        import threading
        threading.Thread(target=atualizar_background).start()
        return jsonify({"status": "iniciado"})
    else:
        return jsonify({"status": "em_progresso"})


@bp_main.route("/progresso")
def progresso_status():
    return jsonify({
        "atualizando": atualizando,
        "progresso": progresso,
        "log": log_texto
    })

bp_graficos = Blueprint("graficos", __name__)


@bp_graficos.route("/grafico/disp")
def grafico_disp():
    indicador = request.args.get("indicador")
    buf = gerar_scatter(df_total, indicador, "mortes_idosos",
                        "Mortalidade vs IDHM")
    return send_file(buf, mimetype="image/png")


@bp_graficos.route("/grafico/reg")
def grafico_reg():
    indicador = request.args.get("indicador")
    buf = gerar_regressao(df_total, indicador, "mortes_idosos",
                          f"Regressão — Mortalidade vs {indicador}")
    return send_file(buf, mimetype="image/png")


@bp_graficos.route("/grafico/heat")
def grafico_heat():
    cols = [
        "IDHM_2010", "IDHM Renda_2010",
        "Renda per capita_2010", "cnes_total", "mortes_idosos"
    ]
    buf = gerar_heatmap(df_total, cols, "Correlação Entre Indicadores")
    return send_file(buf, mimetype="image/png")


@bp_graficos.route("/grafico/bins")
def grafico_bins_route():
    indicador = request.args.get("indicador")
    buf, _ = gerar_bins(df_total, indicador, "mortes_idosos",
                        f"Mortalidade média por faixas de {indicador}", bins=6)
    return send_file(buf, mimetype="image/png")
