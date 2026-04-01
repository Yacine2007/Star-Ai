import os
import requests
import logging
from flask import Flask, request
from pymessenger import Bot
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# إعداد نظام التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد تطبيق Flask
app = Flask(__name__)

# قراءة الإعدادات من متغيرات البيئة
ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
AI_API_URL = os.getenv('AI_API_URL')

# التحقق من وجود التوكن
if not ACCESS_TOKEN:
    raise ValueError("لم يتم العثور على PAGE_ACCESS_TOKEN في ملف .env")
if not VERIFY_TOKEN:
    raise ValueError("لم يتم العثور على VERIFY_TOKEN في ملف .env")

# تهيئة البوت
bot = Bot(ACCESS_TOKEN)

def get_ai_response(user_message):
    """
    إرسال الرسالة إلى API الذكاء الاصطناعي والحصول على الرد
    """
    try:
        # ترميز النص وتجهيز الرابط
        encoded_text = requests.utils.quote(user_message)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        
        logger.info(f"جاري الاتصال بـ API: {AI_API_URL}")
        
        # إرسال الطلب مع مهلة 15 ثانية
        response = requests.get(full_url, timeout=15)
        
        if response.status_code == 200:
            ai_reply = response.text.strip()
            # التأكد من أن الرد ليس فارغًا
            if ai_reply:
                return ai_reply
            else:
                return "🤖 عذرًا، لم أتلقَ ردًا من الخدمة. حاول مرة أخرى."
        else:
            logger.error(f"API error: {response.status_code}")
            return f"⚠️ عذرًا، واجهت مشكلة في الاتصال (الرمز: {response.status_code})"
            
    except requests.exceptions.Timeout:
        logger.error("Timeout error")
        return "⏰ الخدمة لا تستجيب بسرعة كافية. حاول لاحقًا."
    except requests.exceptions.ConnectionError:
        logger.error("Connection error")
        return "🔌 لا يمكن الاتصال بخدمة الذكاء الاصطناعي. تأكد من اتصالك بالإنترنت."
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"❌ حدث خطأ غير متوقع: {str(e)[:100]}"

@app.route("/", methods=['GET', 'POST'])
def webhook():
    """
    نقطة نهاية Webhook لاستقبال الرسائل من فيسبوك ماسنجر
    """
    # التحقق من الرمز (Verification)
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return request.args.get("hub.challenge")
        logger.warning("Invalid verification token")
        return "Verification token mismatch", 403

    # معالجة الرسائل الواردة
    if request.method == 'POST':
        data = request.get_json()
        
        # التأكد من أن الحدث من صفحة
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    # التحقق من وجود رسالة نصية
                    if messaging_event.get('message') and messaging_event['message'].get('text'):
                        sender_id = messaging_event['sender']['id']
                        user_text = messaging_event['message']['text']
                        
                        logger.info(f"رسالة من {sender_id}: {user_text}")
                        
                        # إظهار مؤشر الكتابة
                        try:
                            bot.send_action(sender_id, "typing_on")
                        except:
                            pass
                        
                        # الحصول على الرد من AI
                        ai_reply = get_ai_response(user_text)
                        
                        # إرسال الرد
                        try:
                            bot.send_text_message(sender_id, ai_reply)
                            logger.info(f"تم الرد على {sender_id}")
                        except Exception as e:
                            logger.error(f"فشل إرسال الرد: {str(e)}")
                            # محاولة إرسال رسالة خطأ
                            try:
                                bot.send_text_message(sender_id, "⚠️ عذرًا، حدث خطأ في إرسال الرد.")
                            except:
                                pass
        
        return "ok", 200

@app.route("/health", methods=['GET'])
def health_check():
    """
    نقطة نهاية للتحقق من صحة البوت
    """
    return {"status": "healthy", "bot": "Star Ai"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
