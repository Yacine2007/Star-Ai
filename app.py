import os
import requests
import logging
import json
import time
from flask import Flask, request, jsonify
from datetime import datetime

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

# ========== دالة إرسال الرسائل ==========
def send_message(recipient_id, message_text, retry_count=2):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    for attempt in range(retry_count + 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=15)
            if response.status_code == 200:
                logger.info(f"✅ تم الإرسال إلى {recipient_id}")
                return True
            else:
                logger.error(f"❌ فشل الإرسال: {response.status_code}")
        except Exception as e:
            logger.error(f"⚠️ خطأ: {str(e)}")
        
        if attempt < retry_count:
            time.sleep(2 ** attempt)
    
    return False

# ========== دالة معالجة الأسئلة المخصصة (مختصرة) ==========
def handle_special_queries(user_message):
    msg_lower = user_message.lower()
    
    # سؤال عن الهوية
    if any(word in msg_lower for word in ['من انت', 'من أنت', 'who are you', 'اسمك']):
        return "أنا Star Ai، تم تطويري بواسطة شركة B.Y PRO."
    
    # سؤال عن المطور
    if any(word in msg_lower for word in ['من صنعك', 'مطورك', 'developer', 'المطور']):
        return "تم تطويري بواسطة شركة B.Y PRO."
    
    # سؤال عن الموقع (فقط هنا يظهر الرابط)
    if any(word in msg_lower for word in ['موقع', 'website', 'رابط', 'link', 'الموقع']):
        return f"يمكنك زيارة موقع شركة B.Y PRO عبر الرابط التالي:\n{COMPANY_URL}"
    
    # سؤال عن الشركة (رد مختصر)
    if any(word in msg_lower for word in ['شركة', 'company', 'by pro', 'بي برو']):
        return "أنا من تطوير شركة B.Y PRO."
    
    return None

# ========== دالة الحصول على رد AI ==========
def get_ai_response(user_message):
    # التحقق من الأسئلة المخصصة أولاً
    special_response = handle_special_queries(user_message)
    if special_response:
        logger.info("🎯 سؤال مخصص")
        return special_response
    
    # الاتصال بـ API
    try:
        encoded_text = requests.utils.quote(user_message)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        
        response = requests.get(full_url, timeout=20)
        
        if response.status_code == 200:
            raw = response.text.strip()
            try:
                data = json.loads(raw)
                reply = data.get('response', data.get('text', raw))
            except:
                reply = raw
            
            # تنظيف الرد من أي ذكر لـ Google أو ChatGPT
            unwanted = ['google', 'chatgpt', 'openai', 'gpt', 'bard', 'gemini']
            for term in unwanted:
                if term in reply.lower():
                    reply = reply.replace(term, 'B.Y PRO')
                    reply = reply.replace(term.upper(), 'B.Y PRO')
            
            return reply
        else:
            return "أنا Star Ai من B.Y PRO. كيف يمكنني مساعدتك؟"
            
    except Exception as e:
        logger.error(f"خطأ: {str(e)}")
        return "أنا Star Ai من B.Y PRO. حدث خطأ، حاول مرة أخرى."

# ========== دالة مؤشر الكتابة ==========
def show_typing(sender_id):
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
        data = {
            "recipient": {"id": sender_id},
            "sender_action": "typing_on"
        }
        requests.post(url, json=data, timeout=5)
    except:
        pass

# ========== نقطة النهاية الرئيسية ==========
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
        logger.info("📨 POST received")
        
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
                        
                        show_typing(sender_id)
                        ai_reply = get_ai_response(user_text)
                        send_message(sender_id, ai_reply)
            
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
    app.run(host='0.0.0.0', port=port, debug=False)
