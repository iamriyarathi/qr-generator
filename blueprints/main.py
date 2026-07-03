"""Page routes — everything that renders a template."""
from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/generator")
def generator():
    return render_template("generator.html")


@main_bp.route("/history")
def history():
    return render_template("history.html")


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
