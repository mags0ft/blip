from flask import Flask
from flask_talisman import Talisman
from config import STREAMS


def create_app():
    app = Flask(__name__)

    Talisman(
        app,
        # Allow sources from STREAMS
        content_security_policy={
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "img-src": ["'self'", *STREAMS],
        },
    )

    from app.views import views_bp

    app.register_blueprint(views_bp)

    return app
