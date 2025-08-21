# 📞 Smart Call Assistant – Intelligent Voice Response System  
**By Mohammad Askari **  
<img width="1917" height="977" alt="image" src="https://github.com/user-attachments/assets/571dbc91-47a0-4c92-a7ff-1f9d638075bb" />


## 🚀 Overview  
This project is a **complete intelligent voice assistant system** for phone call centers.  
It processes user speech, understands the intent, generates context-aware responses using a Large Language Model, and returns synthesized voice — all fully automated.

> 💡 Built from scratch without external paid APIs, deployed & tested on real server under constraints.

## 🎯 Core Features

- 🎙️ **Speech-to-Text (STT)** using **OpenAI Whisper**
- 🧠 **Intent Detection & Sentiment Analysis** (Keyword-based + optional Transformers)
- 🤖 **LLM-based Response Generation** (GPT-compatible endpoint)
- 🔊 **Text-to-Speech (TTS)** using **Google Gemini (genai)**
- 🖥️ **Flask-based Web Dashboard** to upload and interact with the system
- 📊 **SQLite Logging** of all calls, processing metrics & quality indicators
- 🧪 **End-to-End and Concurrent Load Testing** tools
- ⚙️ Modular pipeline: audio enhancement → STT → NLP → GPT → TTS → audio playback

## 📁 Project Structure
```
app/
├── audio/              # Audio pre-processing & noise reduction
├── stt/                # Speech-to-text (Whisper)
├── gpt/                # GPT client abstraction (Metis endpoint)
├── tts/                # TTS using Google Gemini
├── analysis/           # Intent and sentiment analysis
├── database/           # SQLite interface and schema
├── templates/          # Flask front-end
├── main.py             # Full pipeline logic
├── app.py              # Flask API and UI
config/
├── .env                # Environment variables
tests/
├── test_system.py      # E2E tests
├── concurrency_test.py # Load testing with concurrency
```

## 🔧 How It Works

1. **User speaks** during a phone call.
2. **Audio is processed** and passed to Whisper → converts speech to text.
3. **Intent & sentiment** extracted from transcript.
4. **LLM (GPT)** generates a context-aware answer using predefined knowledge.
5. **TTS** converts the answer to voice (using Gemini API).
6. **Audio response is played back** to the caller.
7. **Call logs** (duration, quality, timings) are saved to SQLite for monitoring.

## 📷 Demo Screenshot  
_(Add here a screenshot of the Flask UI showing audio upload and response)_  
→ `static/screenshots/demo.png`

## ⚙️ Tech Stack  
- Python 3.11  
- Flask  
- OpenAI Whisper  
- Google genai (TTS)  
- SQLite  
- Transformers (optional for NLP)  
- Gunicorn (production WSGI)  

## 📌 Requirements  
- `pip install -r requirements.txt`  
- Add `.env` file with keys for GPT and Gemini APIs.

## 🚀 Run Instructions

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app/app.py

# Or with Gunicorn (recommended)
gunicorn app.app:app -w 2 -b 0.0.0.0:5000
```

## 📊 Metrics Tracked
- `processing_time` – full pipeline latency
- `gpt_quality` – subjective quality score
- `intent`, `sentiment`, `response_text`
- File paths for input/output audio

<img width="1821" height="581" alt="image" src="https://github.com/user-attachments/assets/203a6b71-a5e1-4c65-b92a-7050ed98d229" />

## 💡 Highlights
- Designed & implemented fully **solo**.
- Delivered under **tight technical limitations** (no paid APIs or DevOps).
- Production-oriented code with modularity, testing, and database integration.
- Real-time & batch audio processing tools included.

## 📎 About the Developer  
👨‍🎓 **Mohammad Askari**  
Final-year Electrical Engineering student @ **University of Tehran**
Interested in **Quantitative Finance, Optimization, AI, and Markets**  

