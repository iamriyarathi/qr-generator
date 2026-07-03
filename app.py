"""
Professional QR Code Generator — Flask application entry point.

Run locally:
    python app.py

Deploy on Vercel: this module exposes a module-level `app` object,
which is exactly what the @vercel/python builder expects to find.
"""
import os

from flask import Flask, render_template

from config import Config
from database import db as db_module


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # Blueprints
    from blueprints.main import main_bp
    from blueprints.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Database
    db_module.init_db(app)

    # Friendly error pages
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return {"success": False, "errors": {"_": "Uploaded file is too large."}}, 413

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    # Security headers on every response.
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    return app


app = create_app()


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug)
