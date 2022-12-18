from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, MessageAction, QuickReplyButton, QuickReply
from api.version import VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH
from api.chatgpt import ChatGPT

import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

app = Flask(__name__)
chatgpt = ChatGPT()

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(f"{event=}")
    global working_status
    if event.message.type != "text":
        return

    if event.message.text == "version":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=(
                f"GPT-Linebot-python-flask-on-vercel, version {VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}. " 
                f"This project is contributed by @howarder3, @w95wayne10."
                )
            )
        )
        return
        

    if event.message.text == "說話":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return

    if event.message.text == "閉嘴":
        working_status = False
        chatgpt.clean_msg()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
        return

    if working_status:
        chatgpt.add_msg(f"Q:{event.message.text}\n")
        if chatgpt.if_contains_word(event.message.text):
            reply_msg = chatgpt.get_long_response()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_msg))
        else:
            reply_msg, finish_response = chatgpt.get_response()
            if finish_response:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_msg))
            else:
                line_bot_api.reply_message(
                    event.reply_token, 
                    TextSendMessage(text=reply_msg,
                        quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(action=MessageAction(label="繼續", text="繼續"))
                            ]
                        )
                    )
                )



            






if __name__ == "__main__":
    app.run()
