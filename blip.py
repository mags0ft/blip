from app import create_app
from app.guard import start_background_job


start_background_job()
app = create_app()
