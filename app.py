import os
import requests
import logging
import json
import time
from flask import Flask, request
from datetime import datetime

# ========== إعدادات التسجيل المتقدمة ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== الإعدادات الأساسية ==========
VERIFY_TOKEN = 'StarAiBot2026Secure'
ACCESS_TOKEN = 'EAA7qyWEuZABEBRIMqFwFkN5vFDa65duXGvh5C4YA3ZBSw90DsGgRQmTIAfhZBqgxPq7KHtDcdKKwKhjmMeXM6zZCfDiRAAzqzZCw2C1SOZCM0l063MFytUXZA1XNXwK5lspJl0mnbEkPVAZAajBZCHGBwAUlHSrQbPCDTM2KuZCo5q5z3WXcp5FjTmXYidVJZCZCEnQPEvC47SXx'
AI_API_URL = 'http://fi8.bot-hosting.net:20163/elos-gemina'

# ========== دالة إرسال الرسائل مع إعادة المحاولة ==========
def send_message(recipient_id, message_text, retry_count=2):
    """إرسال رسالة عبر فيسبوك ماسنجر مع إعادة المحاولة تلقائيًا"""
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    for attempt in range(retry_count + 1):
        try:
            logger.info(f"📤 محاولة إرسال #{attempt + 1} إلى {recipient_id}")
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ تم إرسال الرد بنجاح إلى {recipient_id}")
                return True
            else:
                logger.error(f"❌ فشل الإرسال (HTTP {response.status_code}): {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ مهلة الإرسال انتهت (محاولة {attempt + 1})")
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 خطأ في الاتصال (محاولة {attempt + 1})")
        except Exception as e:
            logger.error(f"⚠️ خطأ غير متوقع في الإرسال: {str(e)}")
        
        if attempt < retry_count:
            wait_time = 2 ** attempt
            logger.info(f"⏳ انتظار {wait_time} ثواني قبل إعادة المحاولة...")
            time.sleep(wait_time)
    
    logger.error(f"💥 فشل إرسال الرسالة إلى {recipient_id} بعد {retry_count + 1} محاولات")
    return False

# ========== دالة الحصول على رد AI ==========
def get_ai_response(user_message):
    """الحصول على رد من API الذكاء الاصطناعي"""
    logger.info(f"🤖 الاتصال بـ AI API...")
    logger.info(f"📝 الرسالة: {user_message[:100]}")
    
    try:
        encoded_text = requests.utils.quote(user_message)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        
        start_time = time.time()
        response = requests.get(full_url, timeout=25)
        elapsed_time = time.time() - start_time
        
        logger.info(f"⏱️ وقت الاستجابة: {elapsed_time:.2f} ثانية")
        logger.info(f"📊 حالة API: HTTP {response.status_code}")
        
        if response.status_code == 200:
            raw_response = response.text.strip()
            logger.info(f"📦 الرد الخام: {raw_response[:200]}")
            
            # معالجة JSON
            try:
                response_data = json.loads(raw_response)
                if 'response' in response_data:
                    final_reply = response_data['response']
                elif 'text' in response_data:
                    final_reply = response_data['text']
                elif 'message' in response_data:
                    final_reply = response_data['message']
                else:
                    final_reply = raw_response
            except:
                final_reply = raw_response
            
            if not final_reply:
                final_reply = "🤖 عذرًا، لم أتلقَ ردًا مناسبًا."
            
            logger.info(f"✨ الرد النهائي: {final_reply[:100]}")
            return final_reply
        else:
            logger.error(f"❌ خطأ في API: {response.status_code}")
            return f"🌟 مرحبًا! أنا Star Ai. رسالتك: '{user_message[:50]}...'"
            
    except requests.exceptions.Timeout:
        logger.error(f"⏰ انتهت المهلة")
        return "⏰ عذرًا، الخدمة بطيئة حاليًا. حاول مرة أخرى."
    except Exception as e:
        logger.error(f"💥 خطأ: {str(e)}")
        return f"💫 مرحبًا بك في Star Ai! أنا هنا لمساعدتك."

# ========== نقطة النهاية الرئيسية ==========
@app.route('/', methods=['GET', 'POST', 'HEAD'])
def webhook():
    """نقطة النهاية الرئيسية للبوت"""
    
    # 1. طلبات HEAD (لـ Render)
    if request.method == 'HEAD':
        logger.info("🔍 HEAD request - 200 OK")
        return '', 200
    
    # 2. طلبات GET
    if request.method == 'GET':
        # التحقق من وجود معاملات فيسبوك
        if 'hub.mode' in request.args:
            logger.info("📥 Facebook verification request")
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                logger.info("✅✅✅ Webhook verified successfully! ✅✅✅")
                return challenge, 200
            else:
                logger.warning(f"❌ Verification failed: token={token}")
                return "Verification failed", 403
        else:
            # طلبات GET عادية من المتصفح
            return "🌟 Star Ai Bot is running! 🌟\nSend a message on Facebook Messenger to chat with me.", 200
    
    # 3. طلبات POST (الرسائل)
    if request.method == 'POST':
        logger.info("="*60)
        logger.info("📨 New POST request received")
        
        try:
            data = request.get_json()
            if not data:
                logger.warning("⚠️ No JSON data")
                return "ok", 200
            
            logger.info(f"📦 Data: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            if data.get('object') != 'page':
                logger.warning(f"⚠️ Unknown object: {data.get('object')}")
                return "ok", 200
            
            for entry in data.get('entry', []):
                for messaging in entry.get('messaging', []):
                    sender_id = messaging.get('sender', {}).get('id')
                    message = messaging.get('message', {})
                    
                    if not sender_id:
                        continue
                    
                    logger.info(f"👤 Sender: {sender_id}")
                    
                    if message and message.get('text'):
                        user_text = message['text']
                        logger.info(f"💬 Message: {user_text}")
                        
                        # إظهار مؤشر الكتابة
                        try:
                            url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
                            requests.post(url, json={"recipient": {"id": sender_id}, "sender_action": "typing_on"}, timeout=5)
                            logger.info("✍️ Typing indicator shown")
                        except:
                            pass
                        
                        # الحصول على الرد
                        ai_reply = get_ai_response(user_text)
                        
                        # إرسال الرد
                        send_message(sender_id, ai_reply)
                        
                    elif message and message.get('attachments'):
                        logger.info("📎 Attachment received")
                        send_message(sender_id, "📎 شكرًا لك! حاليًا أدعم النصوص فقط.")
                    else:
                        logger.info("❓ Unknown message type")
            
            return "ok", 200
            
        except Exception as e:
            logger.error(f"💥 Error: {str(e)}")
            logger.exception("Details:")
            return "ok", 200

# ========== نقاط نهاية إضافية ==========
@app.route('/health', methods=['GET'])
def health():
    return {"status": "healthy", "bot": "Star Ai", "time": datetime.now().isoformat()}, 200

@app.route('/info', methods=['GET'])
def info():
    return {"name": "Star Ai", "status": "running", "version": "2.0"}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Star Ai Bot starting on port {port}")
    logger.info(f"🔑 Verify token: {VERIFY_TOKEN}")
    app.run(host='0.0.0.0', port=port, debug=False)
