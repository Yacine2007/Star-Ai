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
        return response.status_code == 200
    except Exception as e:
        logger.error(f"خطأ في الإرسال: {str(e)}")
        return False

def get_ai_response(user_message):
    """الحصول على رد من API الذكاء الاصطناعي"""
    try:
        encoded_text = requests.utils.quote(user_message)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        logger.info(f"الاتصال بـ AI: {full_url[:100]}...")
        response = requests.get(full_url, timeout=15)
        
        if response.status_code == 200:
            reply = response.text.strip()
            if reply:
                # محاولة استخراج النص من JSON إذا كان الرد JSON
                try:
                    import json
                    reply_data = json.loads(reply)
                    if 'response' in reply_data:
                        reply = reply_data['response']
                except:
                    pass
                return reply
        return f"مرحبًا! أنا Star Ai. رسالتك: '{user_message}'"
    except Exception as e:
        logger.error(f"خطأ في AI: {str(e)}")
        return f"🌟 مرحبًا بك في Star Ai! كيف يمكنني مساعدتك؟"

@app.route('/', methods=['GET'])
def verify():
    """التحقق من Webhook - مهم جداً"""
    # طباعة كل المعاملات للتصحيح
    logger.info(f"جميع المعاملات: {dict(request.args)}")
    
    # فيسبوك يرسل المعاملات بهذه الأسماء
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    logger.info(f"mode: {mode}, token: {token}, challenge: {challenge}")
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logger.info("✅ تم التحقق بنجاح!")
        return challenge, 200
    else:
        logger.warning(f"❌ فشل التحقق. mode={mode}, token={token}")
        return "Verification failed", 403

@app.route('/', methods=['POST'])
def webhook():
    """استقبال الرسائل"""
    data = request.get_json()
    logger.info(f"📨 استلمت POST: {data}")
    
    if data and data.get('object') == 'page':
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
                    except Exception as e:
                        logger.error(f"خطأ في مؤشر الكتابة: {e}")
                    
                    # الحصول على الرد
                    ai_reply = get_ai_response(user_text)
                    
                    # إرسال الرد
                    success = send_message(sender_id, ai_reply)
                    if success:
                        logger.info(f"✅ تم الرد على {sender_id}")
                    else:
                        logger.error(f"❌ فشل إرسال الرد إلى {sender_id}")
    
    return "ok", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
