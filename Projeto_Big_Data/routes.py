# routes.py
from flask import Blueprint, render_template, request, send_file, jsonify
from config import (
    hub, df_total, atualizando, progresso, log_texto,
    atualizar_background
)
from source.modulo_analise import (
    gerar_scatter, gerar_regressao,
    gerar_heatmap, gerar_bins
)


bp_main = Blueprint("main", __name__)


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
                        f"Mortalidade vs {indicador}")
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
