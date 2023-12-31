import atexit
from datetime import datetime, timedelta
import logging
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from config.config import Config

from flask import current_app as app

time_to_live = 24

def allowed_file(filename):
    ALLOWED_EXTENSIONS = app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 


def cleanup_sessions(session_folder: Path, expiration_time: int):
    now = datetime.now()

    for file_path in session_folder.iterdir():
        if file_path.is_file() and file_path.stat().st_mtime < (now - timedelta(minutes=expiration_time)).timestamp():
            try:
                file_path.unlink()
            except Exception as e:
                logging.error(f"Failed to delete {file_path}. Reason: {e}")


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(lambda: cleanup_sessions(Path(Config.SESSION_FILE_DIR), time_to_live), 'interval', hours=time_to_live)

# Ensure all scheduled tasks are stopped when the app is exiting
atexit.register(lambda: scheduler.shutdown())