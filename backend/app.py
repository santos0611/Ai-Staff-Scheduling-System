import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from routes.ai_routes import ai_bp
from routes.auth_routes import auth_bp
from routes.staff_routes import staff_bp
from routes.availability_routes import availability_bp
from routes.shift_routes import shift_bp
from routes.timeoff_routes import timeoff_bp
from routes.notification_routes import notification_bp


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"
load_dotenv(ROOT_DIR / ".env")

app = Flask(__name__)
CORS(app)

# API blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(availability_bp)
app.register_blueprint(shift_bp)
app.register_blueprint(timeoff_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(ai_bp)


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok", "message": "Staff Rota API is running"})


# Serve the portfolio application and frontend assets from the same local Flask server.
@app.get("/")
def index():
    return send_from_directory(PAGES_DIR, "index.html")


@app.get("/<page>.html")
def serve_page(page):
    return send_from_directory(PAGES_DIR, f"{page}.html")


@app.get("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(FRONTEND_DIR / "css", filename)


@app.get("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(FRONTEND_DIR / "js", filename)


@app.get("/images/<path:filename>")
def serve_images(filename):
    return send_from_directory(FRONTEND_DIR / "images", filename)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
