from flask import Blueprint, render_template
from config import STREAMS


views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def home():
    return render_template("home.html", streams=STREAMS)
