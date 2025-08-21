import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

GPT_API_KEY = os.getenv("METIS_API_KEY")
GPT_URL = "https://api.metisai.ir/openai/v1/chat/completions"

def ask_gpt(prompt: str) -> str:
    if not GPT_API_KEY:
        raise ValueError("GPT API key not found. Set METIS_API_KEY in your environment.")

    headers = {
        "Authorization": f"Bearer {GPT_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 256
    }

    try:
        response = requests.post(GPT_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    except requests.Timeout:
        return "خطا: پاسخ از سرویس GPT زمان‌بر شد. لطفاً دوباره تلاش کنید."
    except requests.RequestException as e:
        return f"خطا در ارتباط با سرویس GPT: {e}"
