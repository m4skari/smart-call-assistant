import whisper
import os
import tempfile
from typing import Optional

import librosa
import soundfile as sf
try:
    import torch  # type: ignore
    _torch_available = True
except Exception:
    _torch_available = False

def transcribe_audio(file_path):
    """
    تشخیص گفتار با تنظیمات بهینه برای زبان فارسی
    """
    try:
        print(f"🎵 شروع تشخیص گفتار از فایل: {os.path.basename(file_path)}")
        
        # انتخاب مدل از متغیر محیطی، پیش‌فرض دقیق‌تر برای کیفیت بهتر
        model_name = os.getenv("WHISPER_MODEL", "medium")
        print(f"🔄 بارگذاری مدل Whisper {model_name}...")
        
        try:
            model = whisper.load_model(model_name)
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری مدل {model_name}: {e}")
            fallback_model = os.getenv("WHISPER_FALLBACK_MODEL", "medium")
            print(f"🔄 تلاش با مدل {fallback_model}...")
            model = whisper.load_model(fallback_model)
            model_name = fallback_model

        # پیش‌پردازش صوت: مونو و 16kHz برای پایداری بیشتر
        preprocess_enabled = os.getenv("WHISPER_PREPROCESS", "1") == "1"
        input_path = file_path
        tmp_path: Optional[str] = None
        if preprocess_enabled:
            try:
                audio, sr = librosa.load(file_path, sr=16000, mono=True)
                fd, tmp_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                sf.write(tmp_path, audio, 16000)
                input_path = tmp_path
                print("🧹 پیش‌پردازش صوت انجام شد (mono, 16k)")
            except Exception as e:
                print(f"⚠️ خطا در پیش‌پردازش صوت: {e}. ادامه با فایل اصلی")

        # تنظیمات بهینه و قابل‌پیکربندی
        use_fp16 = _torch_available and torch.cuda.is_available()
        beam_size = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
        best_of = int(os.getenv("WHISPER_BEST_OF", "5"))
        condition_prev = os.getenv("WHISPER_CONDITION_ON_PREVIOUS", "1") == "1"

        result = model.transcribe(
            input_path,
            language=os.getenv("WHISPER_LANGUAGE", "fa"),
            task="transcribe",
            fp16=use_fp16,
            verbose=True,
            temperature=0.0,
            compression_ratio_threshold=float(os.getenv("WHISPER_COMPRESSION_RATIO", "2.4")),
            logprob_threshold=float(os.getenv("WHISPER_LOGPROB_THRESHOLD", "-1.0")),
            no_speech_threshold=float(os.getenv("WHISPER_NO_SPEECH_THRESHOLD", "0.6")),
            condition_on_previous_text=condition_prev,
            initial_prompt=os.getenv("WHISPER_INITIAL_PROMPT", "این یک مکالمه فارسی است"),
            beam_size=beam_size,
            best_of=best_of
        )
        
        transcript = result["text"].strip()
        confidence = result.get("avg_logprob", 0)
        
        print(f"✅ متن تشخیص داده شده: {transcript}")
        print(f"📊 اطمینان: {confidence:.2f}")
        
        # اگر اطمینان کم است و مدل base/medium نیست، با مدل large تلاش کن (اختیاری)
        try_large = os.getenv("WHISPER_TRY_LARGE_ON_LOW_CONF", "1") == "1"
        if try_large and confidence < -1.0 and model_name != "large":
            print("⚠️ اطمینان کم، تلاش با مدل large...")
            try:
                large_model = whisper.load_model("large")
                large_result = large_model.transcribe(
                    input_path,
                    language=os.getenv("WHISPER_LANGUAGE", "fa"),
                    temperature=0.0,
                    verbose=False,
                    beam_size=beam_size,
                    best_of=best_of
                )
                large_transcript = large_result["text"].strip()
                large_confidence = large_result.get("avg_logprob", 0)
                
                if large_confidence > confidence:
                    print(f"✅ مدل large بهتر عمل کرد: {large_transcript}")
                    return large_transcript
                else:
                    print(f"⚠️ مدل large بهتر نبود، استفاده از نتیجه قبلی")
                    return transcript
                    
            except Exception as e:
                print(f"⚠️ خطا در مدل large: {e}")
                return transcript
        
        # پاکسازی فایل موقت در صورت وجود
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

        return transcript
        
    except Exception as e:
        print(f"❌ خطا در تشخیص گفتار: {e}")
        # fallback به مدل کوچک‌تر
        try:
            print("🔄 تلاش با مدل base...")
            model = whisper.load_model("base")
            result = model.transcribe(file_path, language="fa")
            return result["text"].strip()
        except Exception as e2:
            print(f"❌ خطا در مدل fallback: {e2}")
            return "خطا در تشخیص گفتار"
