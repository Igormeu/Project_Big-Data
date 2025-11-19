from flask import Flask, send_file, render_template, request, jsonify
from HubDados import DataHubCE
from modulo_analise import (
    preparar_dados, gerar_scatter, gerar_regressao,
    gerar_heatmap, gerar_bins
)
import threading
import time


app = Flask(__name__)

hub = DataHubCE()

# Variáveis globais de status
atualizando = False
progresso = 0
log_texto = ""

# ============================================================
# Carregar dados ao iniciar
# ============================================================

dados_carregados = False
df_total = None

def atualizar_background():
    global atualizando, progresso, log_texto

    atualizando = True
    progresso = 0
    log_texto = "Iniciando atualização...\n"

    etapas = [
        ("IBGE", lambda: hub.atualizar_dados(atualizar_cnes=False, atualizar_idhm=False, atualizar_mortalidade=False)),
        ("CNES", lambda: hub.atualizar_dados(atualizar_ibge=True, atualizar_idhm=False, atualizar_mortalidade=False)),
        ("IDHM", lambda: hub.atualizar_dados(atualizar_ibge=True, atualizar_cnes=False, atualizar_mortalidade=False)),
        ("Mortalidade", lambda: hub.atualizar_dados(atualizar_ibge=False, atualizar_cnes=False, atualizar_idhm=False)),
    ]

    for i, (nome_etapa, func) in enumerate(etapas, start=1):
        log_texto += f"\n🔄 Atualizando {nome_etapa}...\n"
        progresso = int((i - 1) / len(etapas) * 100)
        func()
        progresso = int(i / len(etapas) * 100)
        log_texto += f"✔️ {nome_etapa} concluído!\n"

        time.sleep(1)  # só para visual ficar bonito

    log_texto += "\n🎉 Atualização finalizada!"
    atualizando = False

def loop_auto_update():
    while True:
        time.sleep(300)  # 5 minutos
        if not atualizando:
            threading.Thread(target=atualizar_background).start()


@app.before_request
def carregar_initial():
    global dados_carregados, df_total
    if not dados_carregados:
        print(">> Carregando dados pela primeira vez...")

        hub = DataHubCE()
        dados = hub.carregar_tudo()
        df_total = preparar_dados(dados["idhm"], dados["cnes"], dados["mortalidade"])

        dados_carregados = True
        print(">> Dados carregados com sucesso!")


# ============================================================
# ROTAS DA INTERFACE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html", titulo="Dashboard Cearense")


# ============================================================
# ROTAS DOS GRÁFICOS
# ============================================================

@app.route("/grafico/disp")
def grafico_disp():
    indicador = request.args.get("indicador")
    buf = gerar_scatter(df_total, indicador, "mortes_idosos",
                        f"Mortalidade vs {indicador}")
    return send_file(buf, mimetype="image/png")

@app.route("/grafico/reg")
def grafico_reg():
    indicador = request.args.get("indicador")
    buf = gerar_regressao(df_total, indicador, "mortes_idosos",
                          f"Regressão — Mortalidade vs {indicador}")
    return send_file(buf, mimetype="image/png")

@app.route("/grafico/heat")
def grafico_heat():
    cols = [
        "IDHM_2010", "IDHM Renda_2010",
        "Renda per capita_2010", "cnes_total", "mortes_idosos"
    ]
    buf = gerar_heatmap(df_total, cols, "Correlação Entre Indicadores")
    return send_file(buf, mimetype="image/png")

@app.route("/grafico/bins")
def grafico_bins_route():
    indicador = request.args.get("indicador")
    buf, _ = gerar_bins(df_total, indicador, "mortes_idosos",
                        f"Mortalidade média por faixas de {indicador}", bins=6)
    return send_file(buf, mimetype="image/png")

# ============================================================
# ROTA ATUALIZAR
# ============================================================

@app.route("/atualizar", methods=["POST"])
def atualizar():
    global atualizando

    if not atualizando:
        threading.Thread(target=atualizar_background).start()
        return jsonify({"status": "iniciado"})
    else:
        return jsonify({"status": "em_progresso"})

@app.route("/progresso")
def progresso_status():
    return jsonify({
        "atualizando": atualizando,
        "progresso": progresso,
        "log": log_texto
    })

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
    threading.Thread(target=loop_auto_update, daemon=True).start()
