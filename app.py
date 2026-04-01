import os
import requests
import logging
import json
import time
import threading
from flask import Flask, request
from datetime import datetime
from collections import defaultdict

# ========== إعدادات التسجيل ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== الإعدادات الأساسية ==========
VERIFY_TOKEN = 'StarAiBot2026Secure'
# استخدم التوكن الطويل الجديد
ACCESS_TOKEN = 'EAA7qyWEuZABEBRFjgX4bmKBfHZBYR6ev5jtW3ZBQubKU4RUXZBj1MRmfDSP0iQk9DgsDzm01rdMBPCewmPr4SwjQZChodouEYjSd7ZBZBKYE1V1yHpiCZBHQ8W2A45yKgTcrbNYdCvpleOHcBy1Uu5cqv51WuNL6NM5fMglhWiNCq1uXv9PCnWFALkFmnP1BJGOyZA1FO2lUZD'
AI_API_URL = 'http://fi8.bot-hosting.net:20163/elos-gemina'
COMPANY_URL = 'https://by-pro.kesug.com/'

# ========== تخزين المحادثات ==========
conversations = defaultdict(list)
MAX_HISTORY = 5

SYSTEM_PROMPT = """أنت Star Ai من B.Y PRO. ردودك مختصرة وسريعة وودودة."""

def send_message(recipient_id, message_text):
    """إرسال رسالة عبر فيسبوك - نسخة مبسطة"""
    try:
        url = "https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": ACCESS_TOKEN}
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "messaging_type": "RESPONSE"
        }
        
        logger.info(f"📤 إرسال إلى {recipient_id}: {message_text[:50]}...")
        
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=10)
        
        logger.info(f"📊 حالة الإرسال: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"✅ تم الإرسال بنجاح")
            return True
        else:
            logger.error(f"❌ فشل: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"⚠️ خطأ: {str(e)}")
        return False

def get_ai_response(user_message, user_id):
    """الحصول على رد من API"""
    try:
        # حفظ رسالة المستخدم
        conversations[user_id].append({"role": "user", "content": user_message})
        
        # بناء السياق
        history = conversations.get(user_id, [])
        context = ""
        for msg in history[-MAX_HISTORY:]:
            if msg["role"] == "user":
                context += f"س: {msg['content']}\n"
            else:
                context += f"ج: {msg['content']}\n"
        
        if context:
            prompt = f"{SYSTEM_PROMPT}\n\n{context}س: {user_message}\nج:"
        else:
            prompt = f"{SYSTEM_PROMPT}\n\nس: {user_message}\nج:"
        
        # الاتصال بـ API
        encoded_text = requests.utils.quote(prompt)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        
        response = requests.get(full_url, timeout=12)
        
        if response.status_code == 200:
            raw = response.text.strip()
            try:
                data = json.loads(raw)
                reply = data.get('response', data.get('text', raw))
            except:
                reply = raw
            
            # تنظيف الرد
            unwanted = ['google', 'chatgpt', 'openai', 'gpt', 'bard', 'gemini']
            for term in unwanted:
                if term in reply.lower():
                    reply = reply.replace(term, 'B.Y PRO')
            
            # حفظ الرد
            conversations[user_id].append({"role": "assistant", "content": reply})
            
            # تنظيف الذاكرة
            if len(conversations[user_id]) > MAX_HISTORY * 2:
                conversations[user_id] = conversations[user_id][-MAX_HISTORY * 2:]
            
            return reply
        else:
            return None
            
    except Exception as e:
        logger.error(f"خطأ API: {str(e)}")
        return None

def process_message(sender_id, user_text):
    """معالجة الرسالة"""
    try:
        # الحصول على الرد
        reply = get_ai_response(user_text, sender_id)
        
        # إذا فشل API، استخدم رد افتراضي
        if not reply:
            reply = "مرحباً! أنا Star Ai من B.Y PRO. كيف يمكنني مساعدتك؟"
        
        # إرسال الرد
        send_message(sender_id, reply)
        
    except Exception as e:
        logger.error(f"خطأ في المعالجة: {str(e)}")
        send_message(sender_id, "عذراً، حدث خطأ. حاول مرة أخرى؟")

# ========== نقاط النهاية ==========
@app.route('/', methods=['GET', 'POST', 'HEAD'])
def webhook():
    if request.method == 'HEAD':
        return '', 200
    
    if request.method == 'GET':
        if 'hub.mode' in request.args:
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                logger.info("✅ Webhook verified")
                return challenge, 200
            return "Verification failed", 403
        else:
            return "Star Ai Bot is running", 200
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or data.get('object') != 'page':
                return "ok", 200
            
            for entry in data.get('entry', []):
                for messaging in entry.get('messaging', []):
                    sender_id = messaging.get('sender', {}).get('id')
                    message = messaging.get('message', {})
                    
                    if sender_id and message and message.get('text'):
                        user_text = message['text']
                        logger.info(f"💬 {sender_id}: {user_text}")
                        
                        # معالجة في خيط منفصل
                        thread = threading.Thread(target=process_message, args=(sender_id, user_text))
                        thread.daemon = True
                        thread.start()
            
            return "ok", 200
            
        except Exception as e:
            logger.error(f"خطأ: {str(e)}")
            return "ok", 200

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Star Ai starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
