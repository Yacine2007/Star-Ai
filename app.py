import os
import requests
import logging
from flask import Flask, request

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# الإعدادات
VERIFY_TOKEN = 'StarAiBot2026Secure'
ACCESS_TOKEN = 'EAA7qyWEuZABEBRIMqFwFkN5vFDa65duXGvh5C4YA3ZBSw90DsGgRQmTIAfhZBqgxPq7KHtDcdKKwKhjmMeXM6zZCfDiRAAzqzZCw2C1SOZCM0l063MFytUXZA1XNXwK5lspJl0mnbEkPVAZAajBZCHGBwAUlHSrQbPCDTM2KuZCo5q5z3WXcp5FjTmXYidVJZCZCEnQPEvC47SXx'
AI_API_URL = 'http://fi8.bot-hosting.net:20163/elos-gemina'

def send_message(recipient_id, message_text):
    """إرسال رسالة عبر فيسبوك"""
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logger.error(f"فشل إرسال الرسالة: {response.text}")
    except Exception as e:
        logger.error(f"خطأ في الإرسال: {str(e)}")

def get_ai_response(user_message):
    """الحصول على رد من API الذكاء الاصطناعي"""
    try:
        encoded_text = requests.utils.quote(user_message)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        response = requests.get(full_url, timeout=15)
        
        if response.status_code == 200:
            reply = response.text.strip()
            if reply:
                return reply
        return f"مرحبًا! أنا Star Ai. رسالتك: '{user_message}'"
    except Exception as e:
        logger.error(f"خطأ في AI: {str(e)}")
        return f"🌟 مرحبًا بك في Star Ai! كيف يمكنني مساعدتك؟"

@app.route('/', methods=['GET'])
def verify():
    """التحقق من Webhook"""
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    logger.info(f"طلب تحقق - token: {token}")
    
    if token == VERIFY_TOKEN:
        logger.info("✅ تم التحقق بنجاح")
        return challenge
    else:
        logger.warning("❌ رمز التحقق غير صحيح")
        return "Verification failed", 403

@app.route('/', methods=['POST'])
def webhook():
    """استقبال الرسائل"""
    data = request.get_json()
    logger.info(f"📨 استلمت بيانات: {data}")
    
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging in entry.get('messaging', []):
                sender_id = messaging.get('sender', {}).get('id')
                message = messaging.get('message', {})
                
                if message and message.get('text'):
                    user_text = message['text']
                    logger.info(f"💬 رسالة من {sender_id}: {user_text}")
                    
                    # إظهار مؤشر الكتابة
                    try:
                        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
                        requests.post(url, json={
                            "recipient": {"id": sender_id},
                            "sender_action": "typing_on"
                        })
                    except:
                        pass
                    
                    # الحصول على الرد
                    ai_reply = get_ai_response(user_text)
                    
                    # إرسال الرد
                    send_message(sender_id, ai_reply)
                    logger.info(f"✅ تم الرد على {sender_id}")
    
    return "ok", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
