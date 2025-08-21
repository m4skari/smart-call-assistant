import time
import uuid
import os
from app.gpt.gpt_client import ask_gpt
from app.analysis.analysis import analyze_text
from app.stt.transcriber import transcribe_audio
from app.database.db import insert_call
from app.audio.enhancement import enhance_audio_file
from app.tts.tts_gemini import synthesize_tts


def _evaluate_gpt_quality(transcript: str, gpt_response: str, intent: str, sentiment: str) -> int:
	"""ارزیابی ساده کیفیت پاسخ GPT (0/1)."""
	try:
		if not gpt_response or len(gpt_response.strip()) < 10:
			return 0
		intent_keywords = {
			"pricing": ["قیمت", "هزینه", "تعرفه", "ریال", "تومان"],
			"product_availability": ["موجود", "موجودی", "در دسترس"],
			"delivery_status": ["ارسال", "پیگیری", "تحویل", "رهگیری"],
			"refund": ["مرجوع", "بازگشت", "استرداد"],
			"complaint": ["پشتیبانی", "مشکل", "عیب", "شکایت"],
			"faq": ["سوال", "پاسخ", "راهنما"]
		}
		kw_list = intent_keywords.get(intent, [])
		if any(kw in gpt_response for kw in kw_list):
			return 1
		return 1 if len(gpt_response.split()) >= 5 else 0
	except Exception:
		return 0


# پردازش تماس‌ها پس از دریافت فایل صوتی
def handle_processed_call(audio_file_path):
	"""
	پردازش فایل صوتی و ذخیره در دیتابیس
	"""
	start_time = time.time()
	
	enhanced_tmp_path = None
	try:
		print(f"🎵 شروع پردازش فایل صوتی: {audio_file_path}")
		
		# مقاوم سازی/بهبود کیفیت صدا
		try:
			enhanced_tmp_path, stats = enhance_audio_file(audio_file_path)
			print(f"🛠️ بهبود صدا انجام شد: {stats}")
		except Exception as e:
			print(f"⚠️ خطا در بهبود صدا: {e}. ادامه با فایل اصلی")
			enhanced_tmp_path = None
		
		# تشخیص گفتار
		input_path = enhanced_tmp_path or audio_file_path
		transcript = transcribe_audio(input_path)
		print(f"✅ متن تشخیص داده شده: {transcript}")
		
		# تحلیل متن
		analysis_result = analyze_text(transcript)
		print(f"🔍 نتیجه تحلیل: {analysis_result}")
		
		# دریافت پاسخ از GPT
		gpt_response = ask_gpt(f"احساسات: {analysis_result['sentiment']}, نیت: {analysis_result['intent']}, متن: {transcript}")
		print(f"🤖 پاسخ GPT: {gpt_response}")
		
		# تولید شناسه یکتا
		unique_id = str(uuid.uuid4())
		
		# تولید صدای ماشینی (اختیاری)
		audio_response_path = None
		if os.getenv("ENABLE_TTS", "0") == "1":
			try:
				meta = synthesize_tts(gpt_response)
				audio_response_path = meta.get("audio_file")
				print(f"🔊 فایل صوتی تولید شد: {audio_response_path}")
			except Exception as e:
				print(f"⚠️ خطا در تولید صدای ماشینی: {e}")
		else:
			print("🎵 TTS غیرفعال است")
		
		# محاسبه زمان پردازش
		processing_time = time.time() - start_time
		print(f"⏱️ زمان پردازش کل: {processing_time:.2f} ثانیه")
		
		# KPI کیفیت پاسخ GPT
		gpt_quality = _evaluate_gpt_quality(transcript, gpt_response, analysis_result['intent'], analysis_result['sentiment'])

		# ذخیره در دیتابیس
		insert_call(unique_id, analysis_result['sentiment'], analysis_result['intent'], gpt_response, transcript, processing_time, audio_response_path, gpt_quality)
		print(f"💾 تماس در دیتابیس ذخیره شد: {unique_id}")
		
		return {
			'success': True,
			'unique_id': unique_id,
			'transcript': transcript,
			'sentiment': analysis_result['sentiment'],
			'intent': analysis_result['intent'],
			'gpt_response': gpt_response,
			'audio_response_path': audio_response_path,
			'processing_time': processing_time,
			'gpt_quality': gpt_quality
		}
		
	except Exception as e:
		processing_time = time.time() - start_time
		print(f"❌ خطا در پردازش تماس: {e}")
		return {
			'success': False,
			'error': str(e),
			'processing_time': processing_time
		}
	finally:
		# پاکسازی فایل موقت بهبود یافته
		try:
			if enhanced_tmp_path and os.path.exists(enhanced_tmp_path):
				os.remove(enhanced_tmp_path)
		except Exception:
			pass

# مثال برای پردازش تماس
if __name__ == "__main__":
	test_file_path = "path/to/test_audio.wav"
	result = handle_processed_call(test_file_path)
	print(f"پاسخ تولید شده: {result}")
