import os
import sqlite3
from app.database.db import get_db_connection
from app.config.config import DB_FILE

def init_db():
    conn = get_db_connection()

    # بررسی وجود جدول
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='call_logs'")
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        # ایجاد جدول جدید با ستون‌های تکمیلی برای KPI و مسیر صوتی
        conn.execute('''CREATE TABLE call_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            unique_id TEXT UNIQUE NOT NULL,
                            sentiment TEXT NOT NULL,
                            intent TEXT NOT NULL,
                            response TEXT NOT NULL,
                            transcript TEXT,
                            processing_time REAL,
                            audio_response_path TEXT,
                            gpt_quality INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        print("✅ جدول call_logs ایجاد شد (با ستون‌های audio_response_path و gpt_quality)")
    else:
        # افزودن ستون‌های جدید در صورت نبود
        cursor.execute("PRAGMA table_info(call_logs)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'audio_response_path' not in columns:
            conn.execute("ALTER TABLE call_logs ADD COLUMN audio_response_path TEXT")
            print("✅ ستون audio_response_path اضافه شد")

        if 'gpt_quality' not in columns:
            conn.execute("ALTER TABLE call_logs ADD COLUMN gpt_quality INTEGER")
            print("✅ ستون gpt_quality اضافه شد")

    conn.commit()
    conn.close()


def reset_db():
    """حذف کامل فایل دیتابیس و ایجاد مجدد جداول."""
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            print(f"🗑️ دیتابیس حذف شد: {DB_FILE}")
        else:
            print("ℹ️ فایل دیتابیس موجود نبود")
    except Exception as e:
        print(f"❌ خطا در حذف دیتابیس: {e}")
        raise
    init_db()

if __name__ == "__main__":
    # اگر RESET_DB=1 باشد، دیتابیس ریست می‌شود
    if os.getenv("RESET_DB", "0") == "1":
        reset_db()
    else:
        init_db()
