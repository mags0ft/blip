from flask import Flask
from flask_talisman import Talisman
from config import STREAMS, Config
from flask_socketio import SocketIO


socketio = SocketIO()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    Talisman(
        app,
        # Allow sources from STREAMS
        content_security_policy={
            "default-src": ["'self'"],
            "script-src": ["'self'", "https://cdn.socket.io"],
            "img-src": ["'self'", *STREAMS],
        },
        force_https=False
    )

    from app.views import views_bp

    app.register_blueprint(views_bp)

    socketio.init_app(app)

    return app
