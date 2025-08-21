import sqlite3
from app.config.config import DB_FILE

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # returns dict-like rows
    return conn

def insert_call(unique_id, sentiment, intent, response, transcript=None, processing_time=None, audio_response_path=None, gpt_quality=None):
    """
    ذخیره اطلاعات تماس در دیتابیس
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO call_logs (unique_id, sentiment, intent, response, transcript, processing_time, audio_response_path, gpt_quality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (unique_id, sentiment, intent, response, transcript, processing_time, audio_response_path, gpt_quality))
        
        conn.commit()
        conn.close()
        
        print(f"✅ تماس با موفقیت در دیتابیس ذخیره شد: {unique_id}")
        return True
        
    except Exception as e:
        print(f"❌ خطا در ذخیره تماس: {e}")
        return False


def get_call_by_unique_id(unique_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM call_logs WHERE unique_id = ?', (unique_id,))
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        print(f"❌ خطا در دریافت تماس: {e}")
        return None


def get_audio_path_by_unique_id(unique_id: str):
    row = get_call_by_unique_id(unique_id)
    if row:
        try:
            return row["audio_response_path"]
        except Exception:
            return None
    return None
