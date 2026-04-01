import os
import requests
import logging
import json
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
        if response.status_code == 200:
            logger.info(f"✅ تم إرسال الرد إلى {recipient_id}")
            return True
        else:
            logger.error(f"فشل الإرسال: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"خطأ في الإرسال: {str(e)}")
        return False

def get_ai_response(user_message):
    """الحصول على رد من API الذكاء الاصطناعي"""
    try:
        encoded_text = requests.utils.quote(user_message)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        logger.info(f"الاتصال بـ AI...")
        response = requests.get(full_url, timeout=20)
        
        if response.status_code == 200:
            reply = response.text.strip()
            # محاولة استخراج النص إذا كان JSON
            try:
                reply_data = json.loads(reply)
                if 'response' in reply_data:
                    reply = reply_data['response']
            except:
                pass
            return reply
        else:
            logger.error(f"AI API error: {response.status_code}")
            return f"مرحبًا! أنا Star Ai. كيف يمكنني مساعدتك؟"
    except Exception as e:
        logger.error(f"AI error: {str(e)}")
        return f"🌟 مرحبًا! أنا Star Ai. رسالتك: {user_message[:50]}..."

@app.route('/', methods=['GET', 'POST', 'HEAD'])
def handle_all():
    """معالجة جميع الطلبات (GET, POST, HEAD)"""
    
    # معالجة طلبات HEAD (يستخدمها Render للتحقق)
    if request.method == 'HEAD':
        return '', 200
    
    # طلبات GET - للتحقق من Webhook
    if request.method == 'GET':
        # طباعة كل شيء للتصحيح
        logger.info(f"GET request with args: {dict(request.args)}")
        
        # فيسبوك يرسل هذه المعاملات للتحقق
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # إذا كان طلب تحقق من فيسبوك
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("✅ Webhook verification successful!")
            return challenge, 200
        
        # إذا كان طلب عادي
        return "Star Ai Bot is running", 200
    
    # طلبات POST - استقبال الرسائل
    if request.method == 'POST':
        logger.info("📨 Received POST request")
        
        try:
            data = request.get_json()
            if not data:
                logger.warning("No JSON data received")
                return "ok", 200
            
            logger.info(f"Data: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            if data.get('object') == 'page':
                for entry in data.get('entry', []):
                    for messaging in entry.get('messaging', []):
                        sender_id = messaging.get('sender', {}).get('id')
                        message = messaging.get('message', {})
                        
                        if message and message.get('text'):
                            user_text = message['text']
                            logger.info(f"💬 From {sender_id}: {user_text}")
                            
                            # إظهار مؤشر الكتابة
                            try:
                                typing_url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
                                requests.post(typing_url, json={
                                    "recipient": {"id": sender_id},
                                    "sender_action": "typing_on"
                                })
                            except:
                                pass
                            
                            # الحصول على الرد
                            ai_reply = get_ai_response(user_text)
                            
                            # إرسال الرد
                            send_message(sender_id, ai_reply)
            
            return "ok", 200
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return "ok", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
