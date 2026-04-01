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
    """
    إرسال رسالة عبر فيسبوك ماسنجر مع إعادة المحاولة تلقائيًا
    """
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
            wait_time = 2 ** attempt  # 1, 2 ثواني
            logger.info(f"⏳ انتظار {wait_time} ثواني قبل إعادة المحاولة...")
            time.sleep(wait_time)
    
    logger.error(f"💥 فشل إرسال الرسالة إلى {recipient_id} بعد {retry_count + 1} محاولات")
    return False

# ========== دالة الحصول على رد AI مع معالجة كاملة ==========
def get_ai_response(user_message):
    """
    الحصول على رد من API الذكاء الاصطناعي مع معالجة شاملة
    """
    logger.info(f"🤖 بدء الاتصال بـ AI API...")
    logger.info(f"📝 الرسالة المرسلة: {user_message[:100]}")
    
    try:
        # ترميز النص
        encoded_text = requests.utils.quote(user_message)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        
        logger.info(f"🌐 عنوان API: {AI_API_URL}")
        
        # إرسال الطلب مع مهلة
        start_time = time.time()
        response = requests.get(full_url, timeout=25)
        elapsed_time = time.time() - start_time
        
        logger.info(f"⏱️ وقت الاستجابة: {elapsed_time:.2f} ثانية")
        logger.info(f"📊 حالة API: HTTP {response.status_code}")
        
        # معالجة الاستجابة الناجحة
        if response.status_code == 200:
            raw_response = response.text.strip()
            logger.info(f"📦 الرد الخام من API: {raw_response[:200]}")
            
            # محاولة فك JSON إذا كان الرد بصيغة JSON
            try:
                response_data = json.loads(raw_response)
                logger.info(f"🔍 تم تحليل الرد كـ JSON بنجاح")
                
                # استخراج النص من حقول محتملة
                if 'response' in response_data:
                    final_reply = response_data['response']
                elif 'text' in response_data:
                    final_reply = response_data['text']
                elif 'message' in response_data:
                    final_reply = response_data['message']
                elif 'reply' in response_data:
                    final_reply = response_data['reply']
                else:
                    final_reply = raw_response
                    
            except json.JSONDecodeError:
                # ليس JSON، استخدم النص كما هو
                logger.info(f"📄 الرد ليس JSON، استخدامه كنص عادي")
                final_reply = raw_response
            
            # التأكد من أن الرد ليس فارغًا
            if not final_reply or final_reply == '':
                logger.warning("⚠️ الرد من API فارغ، استخدام رد افتراضي")
                final_reply = "🤖 عذرًا، لم أتلقَ ردًا مناسبًا. حاول مرة أخرى."
            
            logger.info(f"✨ الرد النهائي: {final_reply[:100]}")
            return final_reply
            
        else:
            # فشل API
            logger.error(f"❌ API أرجأ خطأ: {response.status_code}")
            return f"🌟 مرحبًا! أنا Star Ai. حاليًا الخدمة غير متاحة مؤقتًا. رسالتك: '{user_message[:50]}...'"
            
    except requests.exceptions.Timeout:
        logger.error(f"⏰ انتهت مهلة الاتصال بـ API (أكثر من 25 ثانية)")
        return "⏰ عذرًا، الخدمة بطيئة حاليًا. يرجى المحاولة مرة أخرى بعد قليل."
        
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 فشل الاتصال بـ API - مشكلة في الشبكة")
        return "🔌 لا يمكن الاتصال بخدمة الذكاء الاصطناعي حاليًا. يرجى التحقق من اتصالك بالإنترنت."
        
    except Exception as e:
        logger.error(f"💥 خطأ غير متوقع في AI: {str(e)}")
        return f"💫 مرحبًا بك في Star Ai! أنا هنا لمساعدتك.\n(حدث خطأ فني: {str(e)[:50]})"

# ========== دالة إظهار مؤشر الكتابة ==========
def show_typing(sender_id):
    """إظهار مؤشر الكتابة للمستخدم"""
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
        data = {
            "recipient": {"id": sender_id},
            "sender_action": "typing_on"
        }
        requests.post(url, json=data, timeout=5)
        logger.info(f"✍️ تم إظهار مؤشر الكتابة لـ {sender_id}")
    except Exception as e:
        logger.warning(f"⚠️ فشل إظهار مؤشر الكتابة: {str(e)}")

# ========== نقطة النهاية الرئيسية ==========
@app.route('/', methods=['GET', 'POST', 'HEAD'])
def webhook():
    """نقطة النهاية الرئيسية للبوت"""
    
    # ===== 1. معالجة طلبات HEAD (لـ Render) =====
    if request.method == 'HEAD':
        logger.info("🔍 استلام طلب HEAD - الرد بـ 200")
        return '', 200
    
    # ===== 2. معالجة طلبات GET (التحقق من Webhook) =====
    if request.method == 'GET':
        logger.info("📥 استلام طلب GET")
        logger.info(f"📋 المعاملات: {dict(request.args)}")
        
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        logger.info(f"🔑 mode: {mode}, token: {token}, challenge: {challenge}")
        
        # التحقق من صحة الرمز
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("✅✅✅ تم التحقق من Webhook بنجاح! ✅✅✅")
            return challenge, 200
        else:
            logger.warning(f"❌ فشل التحقق: mode={mode}, token={token}, expected={VERIFY_TOKEN}")
            return "Verification failed", 403
    
    # ===== 3. معالجة طلبات POST (الرسائل) =====
    if request.method == 'POST':
        logger.info("="*60)
        logger.info("📨 استلام طلب POST جديد")
        logger.info(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # قراءة البيانات
            data = request.get_json()
            if not data:
                logger.warning("⚠️ لم يتم استلام أي بيانات JSON")
                return "ok", 200
            
            logger.info(f"📦 البيانات المستلمة: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            # التحقق من نوع الحدث
            if data.get('object') != 'page':
                logger.warning(f"⚠️ نوع الحدث غير مدعوم: {data.get('object')}")
                return "ok", 200
            
            # معالجة الإدخالات
            for entry in data.get('entry', []):
                for messaging in entry.get('messaging', []):
                    sender_id = messaging.get('sender', {}).get('id')
                    
                    if not sender_id:
                        logger.warning("⚠️ لم يتم العثور على معرف المرسل")
                        continue
                    
                    logger.info(f"👤 معرف المرسل: {sender_id}")
                    
                    # التحقق من وجود رسالة
                    message = messaging.get('message', {})
                    if not message:
                        logger.info(f"📭 لا توجد رسالة في هذا الحدث")
                        continue
                    
                    # التحقق من وجود نص
                    if message.get('text'):
                        user_text = message['text']
                        logger.info(f"💬 نص الرسالة: {user_text}")
                        
                        # إظهار مؤشر الكتابة
                        show_typing(sender_id)
                        
                        # الحصول على رد AI
                        ai_reply = get_ai_response(user_text)
                        
                        # إرسال الرد مع إعادة المحاولة
                        success = send_message(sender_id, ai_reply)
                        
                        if success:
                            logger.info(f"🎉 تم الرد على {sender_id} بنجاح")
                        else:
                            logger.error(f"💔 فشل الرد على {sender_id} بعد محاولات متعددة")
                    
                    # التحقق من وجود صور أو مرفقات
                    elif message.get('attachments'):
                        logger.info(f"📎 استلام مرفق من {sender_id}")
                        ai_reply = "📎 شكرًا لك! حاليًا أدعم النصوص فقط. هل تود كتابة رسالة نصية؟"
                        send_message(sender_id, ai_reply)
                    
                    # رسائل فارغة أو غير مدعومة
                    else:
                        logger.info(f"❓ نوع رسالة غير مدعوم من {sender_id}")
                        ai_reply = "💫 مرحبًا! أنا Star Ai. أرجو إرسال رسالة نصية لأتمكن من مساعدتك."
                        send_message(sender_id, ai_reply)
            
            logger.info("✅ تمت معالجة الطلب بنجاح")
            return "ok", 200
            
        except Exception as e:
            logger.error(f"💥 خطأ غير متوقع في معالجة Webhook: {str(e)}")
            logger.exception("تفاصيل الخطأ:")
            return "ok", 200

# ========== نقطة نهاية الصحة ==========
@app.route('/health', methods=['GET'])
def health_check():
    """التحقق من صحة السيرفر"""
    logger.info("🏥 طلب فحص الصحة")
    return {
        "status": "healthy",
        "bot": "Star Ai",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }, 200

# ========== نقطة نهاية للمعلومات ==========
@app.route('/info', methods=['GET'])
def bot_info():
    """معلومات عن البوت"""
    return {
        "name": "Star Ai",
        "description": "بوت ذكاء اصطناعي للدردشة على فيسبوك ماسنجر",
        "status": "running",
        "features": ["text messages", "AI responses", "auto-retry"]
    }, 200

# ========== تشغيل التطبيق ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 بدء تشغيل Star Ai Bot على المنفذ {port}")
    logger.info(f"🔑 رمز التحقق: {VERIFY_TOKEN}")
    logger.info(f"🌐 عنوان API: {AI_API_URL}")
    app.run(host='0.0.0.0', port=port, debug=False)
