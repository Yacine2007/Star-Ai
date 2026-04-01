import os
import requests
import logging
import json
import time
from flask import Flask, request, jsonify
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
ACCESS_TOKEN = 'EAA7qyWEuZABEBRHHyseD3Wet3ks1XeS6puLJEZAhgZBS8QY8SZBI8nT6gmSF212o0fEGBwhuZB1pq8ujYJxc2C89LdtBapBI5oZCo0mZAXcRlLZBdWLHLmlnoaNUYyIh16X3sBJBbH7ILgudzPqETRd5qMGAHEOEVqtO5kZCt3kXTqFZC5KorhXJhJkqDxmrm41YsMY3mqLrTPLiYB52g7MvZBlPdygeZCv0yAjwDmkU9wZDZD'
AI_API_URL = 'http://fi8.bot-hosting.net:20163/elos-gemina'

# ========== روابط الشركة والمنصات ==========
COMPANY_URL = "https://by-pro.kesug.com/"
STORE_PRO_URL = "https://store-pro.by-pro.kesug.com/"
BARMELJ_URL = "https://barmejli.by-pro.kesug.com/"
MAPLINK_URL = "https://maplink.by-pro.kesug.com/"

# ========== معلومات الشركة للردود ==========
COMPANY_INFO = """🌟 **Star Ai** - مساعدك الذكي من **B.Y PRO**

**عن B.Y PRO:**
شركة جزائرية رائدة في مجال التكنولوجيا والبرمجيات، نقدم:
• ✅ برمجيات مخصصة وتطبيقات ذكية
• ✅ حلول الذكاء الاصطناعي وأنظمة التشغيل (Alpha OS)
• ✅ خدمات الصيانة والتطوير التقني
• ✅ دورات تدريبية في البرمجة (Coding Academy)

**منصاتنا:**
• 🛍️ **Store PRO** - متجر برمجيات مجتمعي
• 💻 **barmejLi** - منصة طلبات البرمجة
• 🗺️ **MapLink** - تواصل اجتماعي عبر الخرائط

🔗 **اكتشف المزيد:**
{}

هل تريد معرفة المزيد عن خدماتنا؟ 😊"""

SERVICES_LIST = """🛠️ **خدمات B.Y PRO:**

**1. البرمجة والتطوير:**
• تطوير تطبيقات الهواتف (iOS & Android)
• تصميم مواقع إلكترونية وحلول تجارة إلكترونية
• تطوير بوتات تلجرام وروبوتات الدردشة
• حلول الذكاء الاصطناعي وأنظمة ذكية

**2. التصميم والإبداع:**
• تصميم هويات تجارية وشعارات
• تصميم واجهات المستخدم (UI/UX)
• تصميم جرافيك للمطبوعات والوسائط الرقمية

**3. الصيانة والدعم:**
• صيانة أجهزة الكمبيوتر
• تشخيص المشكلات التقنية
• ترقيع وتحسين الأداء

**4. التسويق الرقمي:**
• زيادة المتابعين والتفاعل
• حملات تسويقية مخصصة
• إدارة حسابات التواصل الاجتماعي

**5. أكاديمية البرمجة:**
• دورات تدريبية معتمدة
• ورش عمل عملية
• شهادات رسمية من B.Y PRO

🔗 **للاستفسار أو طلب الخدمات:**
{}

هل هناك خدمة معينة تهمك؟"""

# ========== دالة إرسال الرسائل مع إعادة المحاولة ==========
def send_message(recipient_id, message_text, retry_count=2):
    """إرسال رسالة عبر فيسبوك ماسنجر مع إعادة المحاولة"""
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
            logger.error(f"⚠️ خطأ غير متوقع: {str(e)}")
        
        if attempt < retry_count:
            wait_time = 2 ** attempt
            logger.info(f"⏳ انتظار {wait_time} ثواني...")
            time.sleep(wait_time)
    
    logger.error(f"💥 فشل الإرسال إلى {recipient_id} بعد {retry_count + 1} محاولات")
    return False

# ========== دالة معالجة الأسئلة المخصصة ==========
def handle_special_queries(user_message):
    """معالجة الأسئلة المخصصة عن البوت والشركة"""
    msg_lower = user_message.lower()
    
    # أسئلة عن هوية البوت
    if any(word in msg_lower for word in ['من انت', 'من أنت', 'who are you', 'what are you', 'اسمك', 'your name', 'من هو']):
        return f"""🌟 أنا **Star Ai**، مساعدك الذكي المصمم خصيصًا لخدمتك!

🛠️ تم تطويري بواسطة شركة **B.Y PRO**، المتخصصة في:
• تطوير البرمجيات والذكاء الاصطناعي
• أنظمة التشغيل (Alpha OS)
• تطبيقات الهواتف والحلول التقنية

💡 **عن B.Y PRO:**
شركة رائدة في مجال التكنولوجيا والبرمجيات، نقدم حلولًا مبتكرة في الذكاء الاصطناعي وتطوير الأنظمة.

🌐 **للمزيد عن خدماتنا ومنتجاتنا:**
{COMPANY_URL}

هل لديك سؤال آخر؟ 😊"""
    
    # أسئلة عن المطور والشركة
    if any(word in msg_lower for word in ['من صنعك', 'مطورك', 'who made you', 'developer', 'المطور', 'شركة', 'company', 'by pro', 'بي برو']):
        return COMPANY_INFO.format(COMPANY_URL)
    
    # أسئلة عن الخدمات
    if any(word in msg_lower for word in ['خدمات', 'خدماتكم', 'ماذا تقدمون', 'services', 'what do you offer', 'شو بتقدم']):
        return SERVICES_LIST.format(COMPANY_URL)
    
    # أسئلة عن الموقع
    if any(word in msg_lower for word in ['موقع', 'website', 'رابط', 'link', 'الموقع', 'صفحة']):
        return f"""🌐 **B.Y PRO** - شركة التكنولوجيا والحلول الذكية

**الرابط الرسمي:**
{COMPANY_URL}

**منصاتنا الأخرى:**
• 🛍️ Store PRO: {STORE_PRO_URL}
• 💻 barmejLi: {BARMELJ_URL}
• 🗺️ MapLink: {MAPLINK_URL}

**ما ستجده في موقعنا:**
• 📱 خدمات البرمجة والتطوير
• 💡 حلول الذكاء الاصطناعي
• 🖥️ نظام Alpha OS
• 📚 أكاديمية البرمجة
• 🛍️ متجر البرمجيات

تفضل بزيارة موقعنا واستكشف خدماتنا! 🚀"""
    
    # أسئلة عن التواصل
    if any(word in msg_lower for word in ['تواصل', 'contact', 'اتصال', 'كيف أتواصل', 'الدعم']):
        return f"""📞 **طرق التواصل مع B.Y PRO:**

**عبر الموقع:**
{COMPANY_URL}

**عبر منصاتنا:**
• 🛍️ Store PRO - متجر البرمجيات
• 💻 barmejLi - منصة طلبات البرمجة

**للاستفسارات والطلبات:**
يمكنك التواصل معنا عبر الموقع الإلكتروني أو عبر منصاتنا المختلفة.

نحن هنا لخدمتك! 💙"""
    
    # أسئلة عن Alpha OS
    if any(word in msg_lower for word in ['alpha', 'نظام', 'os', 'operation', 'تشغيل']):
        return f"""🖥️ **Alpha OS** - نظام تشغيل متقدم

**المميزات:**
• 🔒 أمان محسن وتشفير متقدم
• 🤖 تكامل مع الذكاء الاصطناعي
• 📦 تحديثات مستمرة
• ⚡ أداء عالي وسرعة

**الإصدار الحالي:** Version 26.3

**مبني على:** Linux Kernel

🔗 **للمزيد من المعلومات:**
{COMPANY_URL}

هل تريد معرفة المزيد عن Alpha OS؟"""
    
    return None

# ========== دالة الحصول على رد AI ==========
def get_ai_response(user_message):
    """الحصول على رد من API الذكاء الاصطناعي مع تخصيص هوية البوت"""
    
    # أولاً: التحقق من الأسئلة المخصصة
    special_response = handle_special_queries(user_message)
    if special_response:
        logger.info("🎯 تم التعرف على سؤال مخصص")
        return special_response
    
    # ثانياً: الاتصال بـ API الخارجي
    try:
        encoded_text = requests.utils.quote(user_message)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        
        logger.info(f"🤖 الاتصال بـ API...")
        response = requests.get(full_url, timeout=20)
        
        if response.status_code == 200:
            raw = response.text.strip()
            logger.info(f"📦 الرد الخام: {raw[:200]}")
            
            # معالجة JSON
            try:
                data = json.loads(raw)
                reply = data.get('response', data.get('text', raw))
            except:
                reply = raw
            
            # تنظيف الرد من أي ذكر لـ Google أو ChatGPT
            unwanted_terms = ['google', 'chatgpt', 'openai', 'gpt', 'bard', 'gemini']
            for term in unwanted_terms:
                if term in reply.lower():
                    reply = reply.replace(term, 'B.Y PRO')
                    reply = reply.replace(term.upper(), 'B.Y PRO')
            
            # إضافة تذييل خفيف للردود القصيرة
            if len(reply) < 300 and not any(x in reply.lower() for x in ['by pro', 'star ai', 'by-pro']):
                reply = f"{reply}\n\n✨ *Star Ai* من *B.Y PRO* - {COMPANY_URL}"
            
            logger.info(f"✨ الرد النهائي: {reply[:200]}")
            return reply
            
        else:
            logger.error(f"❌ خطأ API: {response.status_code}")
            return f"🌟 أنا **Star Ai**، مساعدك الذكي من **B.Y PRO**. كيف يمكنني مساعدتك اليوم؟\n\n🔗 اكتشف خدماتنا: {COMPANY_URL}"
            
    except requests.exceptions.Timeout:
        logger.error(f"⏰ انتهت المهلة")
        return f"⏰ عذرًا، الخدمة بطيئة حاليًا.\n\n🌟 **Star Ai** من **B.Y PRO** - {COMPANY_URL}"
    except Exception as e:
        logger.error(f"💥 خطأ AI: {str(e)}")
        return f"🌟 **Star Ai** - مساعدك الذكي من **B.Y PRO**.\n\nآسف، حدث خطأ تقني. يرجى المحاولة مرة أخرى.\n\n🔗 موقعنا: {COMPANY_URL}"

# ========== دالة إظهار مؤشر الكتابة ==========
def show_typing(sender_id):
    """إظهار مؤشر الكتابة"""
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
        data = {
            "recipient": {"id": sender_id},
            "sender_action": "typing_on"
        }
        requests.post(url, json=data, timeout=5)
        logger.info(f"✍️ مؤشر الكتابة لـ {sender_id}")
    except Exception as e:
        logger.warning(f"⚠️ فشل مؤشر الكتابة: {str(e)}")

# ========== نقطة النهاية الرئيسية ==========
@app.route('/', methods=['GET', 'POST', 'HEAD'])
def webhook():
    """نقطة النهاية الرئيسية للبوت"""
    
    # طلبات HEAD
    if request.method == 'HEAD':
        logger.info("🔍 HEAD request - 200 OK")
        return '', 200
    
    # طلبات GET
    if request.method == 'GET':
        if 'hub.mode' in request.args:
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                logger.info("✅✅✅ Webhook verified! ✅✅✅")
                return challenge, 200
            else:
                return "Verification failed", 403
        else:
            return "🌟 Star Ai Bot is running! 🌟\nSend a message on Facebook Messenger to chat with me.", 200
    
    # طلبات POST
    if request.method == 'POST':
        logger.info("="*60)
        logger.info("📨 POST REQUEST RECEIVED")
        
        try:
            data = request.get_json()
            if not data:
                logger.warning("⚠️ No JSON data")
                return "ok", 200
            
            if data.get('object') != 'page':
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
                        
                        show_typing(sender_id)
                        ai_reply = get_ai_response(user_text)
                        send_message(sender_id, ai_reply)
                        
                    elif message and message.get('attachments'):
                        logger.info("📎 Attachment received")
                        send_message(sender_id, "📎 شكرًا لك! حاليًا أدعم النصوص فقط.\n\n✨ *Star Ai* من *B.Y PRO*")
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
    return {"status": "healthy", "bot": "Star Ai", "company": "B.Y PRO", "time": datetime.now().isoformat()}, 200

@app.route('/info', methods=['GET'])
def info():
    return {
        "name": "Star Ai",
        "developer": "B.Y PRO",
        "website": COMPANY_URL,
        "status": "running",
        "version": "2.0"
    }, 200

# ========== تشغيل التطبيق ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Star Ai Bot starting on port {port}")
    logger.info(f"🔑 Verify token: {VERIFY_TOKEN}")
    logger.info(f"🌐 Company website: {COMPANY_URL}")
    app.run(host='0.0.0.0', port=port, debug=False)
