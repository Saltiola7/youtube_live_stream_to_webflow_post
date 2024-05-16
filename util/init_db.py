import logging
import sqlite3
from util.logger import log_function_call

@log_function_call
def init_db(DB):  # Add DB as a parameter
    conn = sqlite3.connect(DB)  # DB is now a parameter
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            webflow_item_id TEXT,
            published_at TEXT,
            downloaded BOOLEAN DEFAULT FALSE,
            uploaded BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()