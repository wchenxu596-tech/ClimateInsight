"""
ClimateInsight API Server
启动: MYSQL_PASSWORD=xxx python app.py
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import CORS_ORIGINS, API_PORT, FLASK_DEBUG

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")
CORS(app, origins=CORS_ORIGINS)

# ── Blueprints ──
from routes.health import bp as health_bp
from routes.dashboard import bp as dashboard_bp
from routes.rankings import bp as rankings_bp
from routes.ai import bp as ai_bp
from routes.agent import bp as agent_bp

app.register_blueprint(health_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(rankings_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(agent_bp)

# ── SPA 静态文件 ──
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def spa(path):
    full = os.path.join(app.static_folder, path)
    if os.path.exists(full) and not os.path.isdir(full):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    print(f" ClimateInsight → http://localhost:{API_PORT}")
    app.run(host="127.0.0.1", port=API_PORT, debug=FLASK_DEBUG)
