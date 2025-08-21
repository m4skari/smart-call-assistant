import os
from dotenv import load_dotenv

# Load from project root .env if present
load_dotenv()
# Also attempt to load from app/config/.env for convenience
_this_dir = os.path.dirname(__file__)
_config_env = os.path.join(_this_dir, '.env')
if os.path.exists(_config_env):
    load_dotenv(_config_env)

# تنظیمات اتصال به پایگاه داده SQLite
DB_FILE = os.getenv("DB_FILE", "call_logs.db")

# تنظیمات API GPT
GPT_API_KEY = os.getenv("METIS_API_KEY")
