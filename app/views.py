from flask import Blueprint, render_template, request, current_app
from config import STREAMS
from app import socketio


views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def home():
    return render_template("home.html", streams=STREAMS)


@views_bp.route("/api/report", methods=["POST"])
def report():
    data = request.json
    message = data.get("message", "")

    if not data.get("secret_key", "") == current_app.config.get("SECRET_KEY"):
        return {"status": "unauthorized"}, 403

    socketio.emit("guard", {"message": message})

    return {"status": "success"}, 200
