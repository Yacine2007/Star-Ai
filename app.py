import os
import requests
import logging
import json
import time
import threading
from flask import Flask, request
from collections import defaultdict

# إعدادات بسيطة
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# الإعدادات
VERIFY_TOKEN = 'StarAiBot2026Secure'
ACCESS_TOKEN = 'EAA7qyWEuZABEBRFjgX4bmKBfHZBYR6ev5jtW3ZBQubKU4RUXZBj1MRmfDSP0iQk9DgsDzm01rdMBPCewmPr4SwjQZChodouEYjSd7ZBZBKYE1V1yHpiCZBHQ8W2A45yKgTcrbNYdCvpleOHcBy1Uu5cqv51WuNL6NM5fMglhWiNCq1uXv9PCnWFALkFmnP1BJGOyZA1FO2lUZD'
AI_API_URL = 'http://fi8.bot-hosting.net:20163/elos-gemina'

# تخزين المحادثات
conversations = defaultdict(list)

def send_message(recipient_id, message_text):
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
        payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
        response = requests.post(url, json=payload, timeout=10)
        logger.info(f"إرسال إلى {recipient_id}: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"خطأ في الإرسال: {e}")
        return False

def get_ai_response(user_message):
    try:
        prompt = f"أنت Star Ai من B.Y PRO. ردودك مختصرة.\nالمستخدم: {user_message}\nStar Ai:"
        response = requests.get(f"{AI_API_URL}?text={requests.utils.quote(prompt)}", timeout=10)
        if response.status_code == 200:
            reply = response.text.strip()
            try:
                reply = json.loads(reply).get('response', reply)
            except:
                pass
            return reply
        return "مرحباً! أنا Star Ai من B.Y PRO."
    except:
        return "مرحباً! أنا Star Ai من B.Y PRO."

def process_message(sender_id, user_text):
    reply = get_ai_response(user_text)
    send_message(sender_id, reply)

# نقاط النهاية
@app.route('/', methods=['GET', 'POST', 'HEAD'])
def webhook():
    # طلبات HEAD (لـ Render)
    if request.method == 'HEAD':
        return '', 200
    
    # طلبات GET (تحقق Webhook)
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        return "Star Ai Bot is running", 200
    
    # طلبات POST (الرسائل)
    if request.method == 'POST':
        data = request.get_json()
        if data and data.get('object') == 'page':
            for entry in data.get('entry', []):
                for msg in entry.get('messaging', []):
                    sender = msg.get('sender', {}).get('id')
                    text = msg.get('message', {}).get('text')
                    if sender and text:
                        logger.info(f"رسالة من {sender}: {text}")
                        threading.Thread(target=process_message, args=(sender, text), daemon=True).start()
        return "ok", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
