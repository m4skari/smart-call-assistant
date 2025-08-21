from flask import Flask, render_template, request, jsonify, send_file
from app.database.db import get_db_connection, get_audio_path_by_unique_id
from app.main import handle_processed_call
from app.database.init_db import init_db
import os
import uuid
from werkzeug.utils import secure_filename
from app.tts.tts_gemini import synthesize_tts

app = Flask(__name__, template_folder='../templates')

# تنظیمات آپلود فایل
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'storage/recordings')
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg'}
# ریشه پروژه (یک سطح بالاتر از پوشه app)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


if not os.path.exists(UPLOAD_FOLDER):
	os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# اطمینان از آماده بودن دیتابیس
init_db()

@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    # قبلاً: cursor.execute("SELECT * FROM call_logs")
    cursor.execute("SELECT * FROM call_logs ORDER BY id DESC")  # یا created_at DESC
    calls = cursor.fetchall()
    conn.close()

    call_data = [dict(call) for call in calls]
    return render_template("index.html", calls=call_data)


@app.route('/play_audio/<unique_id>')
def play_audio(unique_id):
	audio_path = get_audio_path_by_unique_id(unique_id)
	if not audio_path or not os.path.exists(audio_path):
		return jsonify({'success': False, 'error': 'فایل صوتی موجود نیست'}), 404
	return send_file(audio_path)


@app.route('/download_audio/<unique_id>')
def download_audio(unique_id):
	audio_path = get_audio_path_by_unique_id(unique_id)
	if not audio_path or not os.path.exists(audio_path):
		return jsonify({'success': False, 'error': 'فایل صوتی موجود نیست'}), 404
	return send_file(audio_path, as_attachment=True, download_name=os.path.basename(audio_path))

@app.route("/process_audio", methods=['POST'])
def process_audio():
	try:
		if 'audio' not in request.files:
			return jsonify({'success': False, 'error': 'فایل صوتی یافت نشد'})
		
		file = request.files['audio']
		if file.filename == '':
			return jsonify({'success': False, 'error': 'فایلی انتخاب نشده است'})
		
		if file and allowed_file(file.filename):
			# ایجاد نام فایل امن
			filename = secure_filename(file.filename)
			unique_id = str(uuid.uuid4())[:8]
			filename = f"{unique_id}_{filename}"
			
			# ذخیره فایل
			filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			file.save(filepath)
			
			# پردازش فایل صوتی
			try:
				result = handle_processed_call(filepath)
				return jsonify({
					'success': True, 
					'message': 'فایل صوتی با موفقیت پردازش شد',
					'result': result
				})
			except Exception as e:
				return jsonify({
					'success': False, 
					'error': f'خطا در پردازش فایل صوتی: {str(e)}'
				})
		else:
			return jsonify({
				'success': False, 
				'error': 'فرمت فایل پشتیبانی نمی‌شود. فرمت‌های مجاز: wav, mp3, m4a, flac, ogg'
			})
			
	except Exception as e:
		return jsonify({'success': False, 'error': f'خطای سرور: {str(e)}'})

@app.route("/api/calls")
def api_calls():
	"""API endpoint برای دریافت لیست تماس‌ها"""
	conn = get_db_connection()
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM call_logs ORDER BY id DESC")
	calls = cursor.fetchall()
	conn.close()
	
	calls_list = []
	for call in calls:
		row = dict(call)
		calls_list.append({
			'id': row.get('id'),
			'unique_id': row.get('unique_id'),
			'sentiment': row.get('sentiment'),
			'intent': row.get('intent'),
			'response': row.get('response'),
			'transcript': row.get('transcript'),
			'processing_time': row.get('processing_time'),
			'created_at': row.get('created_at')
		})
	
	return jsonify({'calls': calls_list, 'total': len(calls_list)})

# مسیرهای مربوط به فایل صوتی حذف شده‌اند

@app.route("/process_asterisk", methods=['POST'])
def process_asterisk():
	"""پردازش فایل ضبط‌شده توسط Asterisk با دریافت نام فایل

	ورودی:
	  - filename: نام فایل داخل دایرکتوری ضبط Asterisk
	"""
	try:
		filename = None
		if request.form and 'filename' in request.form:
			filename = request.form.get('filename')
		elif request.is_json and request.get_json(silent=True):
			filename = request.get_json().get('filename')

		if not filename:
			return jsonify({'success': False, 'error': 'پارامتر filename الزامی است'}), 400

		asterisk_dir = os.getenv('ASTERISK_MONITOR_DIR', '/app/asterisk-monitor')
		filepath = os.path.join(asterisk_dir, filename)

		if not os.path.exists(filepath):
			return jsonify({'success': False, 'error': f'فایل یافت نشد: {filename}'}), 404

		result = handle_processed_call(filepath)
		return jsonify({'success': True, 'message': 'فایل با موفقیت پردازش شد', 'result': result})
	except Exception as e:
		return jsonify({'success': False, 'error': f'خطای سرور: {str(e)}'}), 500

# قابلیت TTS
@app.route('/tts', methods=['POST'])
def tts_route():
	"""تولید صدای ماشینی با Talkbot
	ورودی JSON: {text, server?, lang?, voice?, gender?}
	"""
	try:
		payload = request.get_json(silent=True) or {}
		text = payload.get('text')
		if not text:
			return jsonify({'success': False, 'error': 'پارامتر text الزامی است'}), 400
		meta = synthesize_tts(
			text=text,
			lang=payload.get('lang'),
			voice=payload.get('voice'),
			gender=payload.get('gender'),
			server=payload.get('server')
		)
		return jsonify({'success': True, 'result': meta})
	except Exception as e:
		return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
	app.run(debug=True)