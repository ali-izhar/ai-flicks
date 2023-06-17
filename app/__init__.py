import os
import secrets
from datetime import datetime, timedelta
from flask import Flask
from flask_session import Session
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

time_to_live = 3*60 # 3 minutes

app = Flask(__name__, template_folder='frontend', static_folder='frontend/assets')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(BASE_DIR, '..', 'flask_session')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=time_to_live)
Session(app)

def cleanup_sessions(session_folder: Path, expiration_time: int):
    now = datetime.now()

    for file_path in session_folder.iterdir():
        if file_path.is_file() and file_path.stat().st_mtime < (now - timedelta(seconds=expiration_time)).timestamp():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(lambda: cleanup_sessions(Path(app.config['SESSION_FILE_DIR']), time_to_live), 'interval', minutes=time_to_live)

# avoid circular import
from app import routes