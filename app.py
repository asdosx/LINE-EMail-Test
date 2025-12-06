from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlencode
import uuid

app = Flask(__name__)

# ====== LINE API 設定 ======
LINE_CHANNEL_ACCESS_TOKEN = "你的 access token"
LINE_CHANNEL_SECRET = "你的 secret"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ====== 你的伺服器 domain ======
SERVER_DOMAIN = "https://your-domain.com"  # Render or Fly.io domain


# ====== 1. LINE Webhook ======
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ====== 2. 當收到 LINE 訊息（指令） ======
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    if user_text.startswith("測試寄信"):
        # 解析 email
        parts = user_text.split()
        if len(parts) < 2:
            reply(event.reply_token, "請提供 email，例如：測試寄信 test@gmail.com")
            return
        
        email = parts[1]

        # 產生 token
        token = str(uuid.uuid4())

        # 建立回報 URL
        report_url = f"{SERVER_DOMAIN}/report?token={token}"

        # 寄信
        send_test_mail(email, report_url)

        reply(event.reply_token, f"已寄出測試信到 {email}\n請查看信箱並點擊確認連結")
        return

    # 其他訊息
    reply(event.reply_token, "請輸入指令：測試寄信 <email>")


# ====== 3. 寄信 function ======
def send_test_mail(to_email, report_url):
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "你的gmail帳號"
    smtp_pass = "你的應用程式密碼"

    subject = "LINE Bot 寄信測試"
    body = f"請點擊下面連結確認您已收到此信：\n{report_url}"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["To"] = to_email
    msg["From"] = smtp_user

    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_pass)
    server.sendmail(smtp_user, [to_email], msg.as_string())
    server.quit()


# ====== 4. 回報 URL ======
@app.route("/report", methods=['GET'])
def report():
    token = request.args.get("token", "").strip()
    if not token:
        return "Invalid token", 400

    # 通知 LINE（這裡你也可以存 token 狀態，這裡直接回 LINE）
    line_bot_api.broadcast(TextSendMessage(text=f"📬 寄信測試成功！（token: {token}）"))

    return "已收到您的回覆，感謝！"


# ====== 启动服务 ======
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
