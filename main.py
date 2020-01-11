from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import ImageMessage, MessageEvent, TextMessage, TextSendMessage
import requests, json, os, io

#import cv2

from io import BytesIO
from PIL import Image
import numpy as np
#from keras.models import load_model

app = Flask(__name__)


#YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
#YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

YOUR_CHANNEL_ACCESS_TOKEN = "p4BEAqE7zT8pOn6LENwtE1FD9zyinlqHDzy6eN/uTPFWVMJTFMpfgJs+8/M8dCKpjyKC+qv7ahrgNBGX1YoMMKIXomjJadubZoTwQyUr0KyK68Gvv4lyDkIydguzLhE4KiclgrpDRptoBo9E/4/dDgdB04t89/1O/w1cDnyilFU="
YOUR_CHANNEL_SECRET = "5796b132d667a820bfe0c1e8b23eb477"

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

header = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + YOUR_CHANNEL_ACCESS_TOKEN
}

# model はグローバルで宣言し、初期化しておく
model = None

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# テキストを受け取る部分
@handler.add(MessageEvent, message=TextMessage)
def handler_message(event):
     line_bot_api.reply_message(
         event.reply_token,
         TextSendMessage(text=event.message.text))

# オウム返しする部分。おまけ。
def reply_message(event, messages):
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )

# 画像を受け取る部分
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print("handle_image:", event)

    message_id = event.message.id
    pix_value = getImageLine(message_id)

    line_bot_api.reply_message(
        event.reply_token,
        messages=pix_value,
        )
#    try:
#        image_text = get_text_by_ms(image_url=getImageLine(message_id))

#        messages = [
#            TextSendMessage(text=image_text),
#        ]

#        reply_message(event, messages)

#    except Exception as e:
#        reply_message(event, TextSendMessage(text='エラーが発生しました'))

def getImageLine(id):

    line_url = 'https://api.line.me/v2/bot/message/' + id + '/content/'

    # 画像の取得
    result = requests.get(line_url, headers=header)
    print(result)

    # 画像の保存
    im = Image.open(BytesIO(result.content))
    #jpgで保存
    image_url = '/tmp/' + id + '.jpg'
    print(image_url)
    im.save(image_url)

    #画像URLからPILで画像を読み込む
    image = Image.open(image_url)
    if image is None:
        print("Not Open..")
    else:
        print("Open Success!!")

    #画像数値処理
    b,g,r = image.split()
    img = image.resize((32,32))
    img_array = img_to_array(img)
    if r > 100:
        result = "このミカンはうまいぞ"
    else:
        resutl = "こんなんミカンじゃねえ"

    return result

def get_text_by_ms(image_url):
    # 90行目のim.saveで保存した url から画像を書き出す。(open-cv version)
    #image = cv2.imread(image_url)
    #if image is None:
    #    print("Not open")
    #b,g,r = cv2.split(image)
    #image = cv2.merge([r,g,b])
    #img = cv2.resize(image,(64,64))
    #img=np.expand_dims(img,axis=0)

    # 90行目のim.saveで保存した url から画像を書き出す。(PIL version)
    image = np.array(Image.open(image_url))
    if image is None:
        print("Not open")
    b,g,r = image.split()
    img = image.resize((32,32))
    img = np.expand_dims(img,axis=0)

    #AIのモデルを動かす所
    # face = detect_who(img=img)

    text = "image road OK"
    return text

def detect_who(img):

    face=""
    # グローバル変数を取得する
    global model

    # 一番初めだけ model をロードしたい
    if model is None:
        model = load_model('./shiogao_model2.h5')

    predict = model.predict(img)
    faceNumLabel=np.argmax(predict)

    if faceNumLabel == 0:
        face = "オリーブオイル顔"
    elif faceNumLabel == 1:
        face = "塩顔"
    elif faceNumLabel == 2:
        face = "しょうゆ顔"
    elif faceNumLabel == 3:
        face = "ソース顔"
    return face

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
