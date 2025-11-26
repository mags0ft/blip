import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


if not os.getenv("SECRET_KEY"):
    raise ValueError("No SECRET_KEY set. Please set it in your .env file.")


STREAMS = [
    "http://192.168.178.89:8090",
]
OLLAMA_HOST = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-vl:4b")
NTFY_CHANNEL = os.environ.get("NTFY_CHANNEL", "guard")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
