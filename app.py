import os
import requests
import logging
import json
import time
import threading
from flask import Flask, request
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# ========== إعدادات التسجيل ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== الإعدادات الأساسية ==========
VERIFY_TOKEN = 'StarAiBot2026Secure'
ACCESS_TOKEN = 'EAA7qyWEuZABEBRHHyseD3Wet3ks1XeS6puLJEZAhgZBS8QY8SZBI8nT6gmSF212o0fEGBwhuZB1pq8ujYJxc2C89LdtBapBI5oZCo0mZAXcRlLZBdWLHLmlnoaNUYyIh16X3sBJBbH7ILgudzPqETRd5qMGAHEOEVqtO5kZCt3kXTqFZC5KorhXJhJkqDxmrm41YsMY3mqLrTPLiYB52g7MvZBlPdygeZCv0yAjwDmkU9wZDZD'
AI_API_URL = 'http://fi8.bot-hosting.net:20163/elos-gemina'
COMPANY_URL = 'https://by-pro.kesug.com/'

# ========== تخزين المحادثات ==========
conversations = defaultdict(list)
MAX_HISTORY = 5  # تقليل عدد الرسائل المحفوظة لزيادة السرعة

# ========== برومبت مبسط ==========
SYSTEM_PROMPT = """أنت Star Ai من B.Y PRO. ردودك مختصرة وسريعة وودودة."""

def get_ai_response_async(user_message, user_id):
    """الحصول على رد من API بشكل غير متزامن"""
    try:
        # بناء برومبت مبسط
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
        
        encoded_text = requests.utils.quote(prompt)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        
        # تقليل وقت المهلة
        response = requests.get(full_url, timeout=12)
        
        if response.status_code == 200:
            raw = response.text.strip()
            try:
                data = json.loads(raw)
                reply = data.get('response', data.get('text', raw))
            except:
                reply = raw
            
            # تنظيف سريع
            unwanted = ['google', 'chatgpt', 'openai', 'gpt', 'bard', 'gemini']
            for term in unwanted:
                if term in reply.lower():
                    reply = reply.replace(term, 'B.Y PRO')
            
            return reply
        else:
            return None
            
    except Exception as e:
        logger.error(f"خطأ: {str(e)}")
        return None

def send_message_async(recipient_id, message_text):
    """إرسال رسالة بشكل غير متزامن"""
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
        headers = {"Content-Type": "application/json"}
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ تم الإرسال إلى {recipient_id}")
            return True
        else:
            logger.error(f"فشل: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"خطأ: {str(e)}")
        return False

def process_message(sender_id, user_text):
    """معالجة الرسالة في خيط منفصل"""
    try:
        # حفظ رسالة المستخدم
        conversations[sender_id].append({"role": "user", "content": user_text})
        
        # الحصول على الرد
        reply = get_ai_response_async(user_text, sender_id)
        
        # إذا فشل الرد، استخدم رد افتراضي
        if not reply:
            # ردود افتراضية سريعة
            default_replies = [
                "مرحباً! كيف我可以 مساعدتك؟",
                "أهلاً! أنا Star Ai من B.Y PRO.",
                "كيف حالك؟ أنا هنا للمساعدة.",
                "أنا Star Ai، تفضل اسأل ما تريد."
            ]
            import random
            reply = random.choice(default_replies)
        
        # حفظ الرد
        conversations[sender_id].append({"role": "assistant", "content": reply})
        
        # الاحتفاظ بآخر الرسائل فقط
        if len(conversations[sender_id]) > MAX_HISTORY * 2:
            conversations[sender_id] = conversations[sender_id][-MAX_HISTORY * 2:]
        
        # إرسال الرد
        send_message_async(sender_id, reply)
        
    except Exception as e:
        logger.error(f"خطأ في المعالجة: {str(e)}")
        # محاولة إرسال رد افتراضي
        send_message_async(sender_id, "عذراً، حدث خطأ. جرب مرة أخرى؟")

# ========== أمر مسح المحادثة ==========
def handle_reset(user_message, user_id):
    msg_lower = user_message.lower()
    reset_words = ['انسى', 'reset', 'clear', 'مسح', 'ابدأ من جديد', 'ننسى']
    if any(word in msg_lower for word in reset_words):
        if user_id in conversations:
            conversations[user_id] = []
        return True
    return False

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
                        logger.info(f"💬 {sender_id}: {user_text[:50]}")
                        
                        # التحقق من أمر المسح
                        if handle_reset(user_text, sender_id):
                            send_message_async(sender_id, "تم مسح ذاكرتي! كيف حالك؟")
                            continue
                        
                        # معالجة الرسالة في خيط منفصل (لا تنتظر)
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
