from routes import bp_main, bp_graficos   # evita circular import
from flask import Flask

app = Flask(__name__)
app.config["SECRET_KEY"] = "CEARÁ-DADOS-2025"
app.register_blueprint(bp_main)
app.register_blueprint(bp_graficos)

if __name__ == "__main__":
    app.run(debug=True)
