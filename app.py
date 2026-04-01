import os
import requests
import logging
import json
import time
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
ACCESS_TOKEN = 'EAA7qyWEuZABEBRHHyseD3Wet3ks1XeS6puLJEZAhgZBS8QY8SZBI8nT6gmSF212o0fEGBwhuZB1pq8ujYJxc2C89LdtBapBI5oZCo0mZAXcRlLZBdWLHLmlnoaNUYyIh16X3sBJBbH7ILgudzPqETRd5qMGAHEOEVqtO5kZCt3kXTqFZC5KorhXJhJkqDxmrm41YsMY3mqLrTPLiYB52g7MvZBlPdygeZCv0yAjwDmkU9wZDZD'
AI_API_URL = 'http://fi8.bot-hosting.net:20163/elos-gemina'
COMPANY_URL = 'https://by-pro.kesug.com/'

# ========== تخزين المحادثات ==========
conversations = defaultdict(list)
MAX_HISTORY = 8  # عدد الرسائل التي يتم تذكرها

# ========== البرومبت الأساسي للبوت ==========
SYSTEM_PROMPT = """أنت Star Ai، مساعد ذكي ودود تم تطويره بواسطة شركة B.Y PRO.
تحدث بطريقة طبيعية ولطيفة، ليست رسمية جداً.
عند سؤالك عن هويتك، قل أنك Star Ai من B.Y PRO.
إذا سأل المستخدم عن موقع الشركة، أعطه الرابط: https://by-pro.kesug.com/
لا تذكر Google أو ChatGPT أو OpenAI، أنت من B.Y PRO.
حافظ على سياق المحادثة وتذكر ما قاله المستخدم سابقاً.
ردودك مختصرة وواضحة."""

def build_prompt(user_id, user_message):
    """بناء البرومبت الكامل مع السياق"""
    history = conversations.get(user_id, [])
    
    # بناء نص المحادثة السابقة
    conversation_text = ""
    for msg in history[-MAX_HISTORY:]:
        if msg["role"] == "user":
            conversation_text += f"المستخدم: {msg['content']}\n"
        else:
            conversation_text += f"Star Ai: {msg['content']}\n"
    
    # البرومبت النهائي
    if conversation_text:
        prompt = f"""{SYSTEM_PROMPT}

المحادثة السابقة:
{conversation_text}
المستخدم: {user_message}
Star Ai:"""
    else:
        prompt = f"""{SYSTEM_PROMPT}

المستخدم: {user_message}
Star Ai:"""
    
    return prompt

def get_ai_response(user_message, user_id):
    """الحصول على رد من API مع السياق الكامل"""
    
    # حفظ رسالة المستخدم
    conversations[user_id].append({"role": "user", "content": user_message})
    
    # بناء البرومبت مع السياق
    prompt = build_prompt(user_id, user_message)
    
    logger.info(f"📝 البرومبت المرسل (مختصر): {prompt[:200]}...")
    
    # الاتصال بـ API
    try:
        encoded_text = requests.utils.quote(prompt)
        full_url = f"{AI_API_URL}?text={encoded_text}"
        
        response = requests.get(full_url, timeout=25)
        
        if response.status_code == 200:
            raw = response.text.strip()
            logger.info(f"📦 الرد الخام: {raw[:200]}")
            
            # معالجة الرد
            try:
                data = json.loads(raw)
                reply = data.get('response', data.get('text', raw))
            except:
                reply = raw
            
            # تنظيف الرد من أي ذكر لـ Google/ChatGPT
            unwanted = ['google', 'chatgpt', 'openai', 'gpt', 'bard', 'gemini']
            for term in unwanted:
                if term in reply.lower():
                    reply = reply.replace(term, 'B.Y PRO')
            
            # حفظ الرد في التاريخ
            conversations[user_id].append({"role": "assistant", "content": reply})
            
            # الاحتفاظ بآخر MAX_HISTORY*2 رسائل فقط
            if len(conversations[user_id]) > MAX_HISTORY * 2:
                conversations[user_id] = conversations[user_id][-MAX_HISTORY * 2:]
            
            return reply
        else:
            fallback = "عذراً، عندي مشكلة في الاتصال حالياً. جرب تسألني مرة ثانية؟"
            conversations[user_id].append({"role": "assistant", "content": fallback})
            return fallback
            
    except Exception as e:
        logger.error(f"خطأ: {str(e)}")
        fallback = "حصل عطل بسيط، جرب تسألني تاني؟"
        conversations[user_id].append({"role": "assistant", "content": fallback})
        return fallback

# ========== أمر مسح المحادثة ==========
def handle_reset(user_message, user_id):
    msg_lower = user_message.lower()
    if any(word in msg_lower for word in ['انسى', 'reset', 'clear', 'مسح', 'ابدأ من جديد']):
        if user_id in conversations:
            conversations[user_id] = []
        return True
    return False

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
        except Exception as e:
            logger.error(f"خطأ: {str(e)}")
        
        if attempt < retry_count:
            time.sleep(2 ** attempt)
    
    return False

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
                        
                        # التحقق من أمر مسح المحادثة
                        if handle_reset(user_text, sender_id):
                            reply = "تم مسح ذاكرتي! لنبدأ من جديد. كيف حالك؟"
                            send_message(sender_id, reply)
                            continue
                        
                        show_typing(sender_id)
                        ai_reply = get_ai_response(user_text, sender_id)
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
