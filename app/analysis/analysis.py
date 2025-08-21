import os

SENTIMENT_NEGATIVE = ["بد", "ناراضی", "عصبانی"]
SENTIMENT_POSITIVE = ["خوشحال", "راضی", "خوب"]
INTENT_KEYWORDS = {
	"pricing": ["قیمت", "هزینه", "چقدر", "هزینه‌ای"],
	"product_availability": ["موجودی", "در دسترس", "موجود", "دارید", "هست", "یافت", "پیدا"],
	"delivery_status": ["ارسال", "تحویل", "رسیدن", "زمان", "کمتر"],
	"refund": ["مرجوعی", "بازگشت وجه", "پس دادن", "تعویض"],
	"complaint": ["شکایت", "مشکل", "خراب", "نقص", "بد"]
}

# بارگذاری تنبل Transformer برای تحلیل احساسات دقیق (در صورت موجود بودن)
_transformers_available = False
try:
	from transformers import pipeline  # type: ignore
	_transformers_available = True
except Exception:
	_transformers_available = False

_sentiment_pipeline = None

def _get_sentiment_pipeline():
	global _sentiment_pipeline
	if _sentiment_pipeline is None:
		model_name = os.getenv("SENTIMENT_MODEL_NAME", "cardiffnlp/twitter-xlm-roberta-base-sentiment")
		# pipeline به‌صورت پیش‌فرض CPU را استفاده می‌کند
		_sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)
	return _sentiment_pipeline

def detect_sentiment_hf(text: str) -> str:
	"""تحلیل احساسات با مدل قوی چندزبانه. خروجی: positive/negative/neutral"""
	if not _transformers_available:
		raise RuntimeError("Transformers is not available")
	pipe = _get_sentiment_pipeline()
	# محدودیت طول برای کارایی
	result = pipe(text[:512])[0]
	label = str(result.get("label", "")).lower()
	# نگاشت برچسب‌ها به positive/negative/neutral
	if "pos" in label:
		return "positive"
	if "neg" in label:
		return "negative"
	return "neutral"

def detect_sentiment_keyword(text: str) -> str:
	for neg in SENTIMENT_NEGATIVE:
		if neg in text:
			return "negative"
	for pos in SENTIMENT_POSITIVE:
		if pos in text:
			return "positive"
	return "neutral"

def detect_intent(text: str) -> str:
	for intent, kw_list in INTENT_KEYWORDS.items():
		for kw in kw_list:
			if kw in text:
				return intent
	return "faq"  # fallback

def analyze_text(transcript: str):
	backend = os.getenv("SENTIMENT_BACKEND", "hybrid").lower()
	if backend == "hf":
		try:
			sentiment = detect_sentiment_hf(transcript)
		except Exception:
			# در صورت نبود یا خطا، بازگشت به روش کلیدواژه
			sentiment = detect_sentiment_keyword(transcript)
	elif backend == "hybrid":
		# ابتدا کلیدواژه؛ اگر مبهم بود (neutral)، به مدل قوی مراجعه کن
		sentiment_kw = detect_sentiment_keyword(transcript)
		if sentiment_kw == "neutral":
			try:
				sentiment = detect_sentiment_hf(transcript)
			except Exception:
				sentiment = sentiment_kw
		else:
			sentiment = sentiment_kw
	else:
		# backend == keyword
		sentiment = detect_sentiment_keyword(transcript)

	intent = detect_intent(transcript)
	return {
		"sentiment": sentiment,
		"intent": intent
	}
