#ライブラリのimport

##アプリケーションんのフレームワークとしてFlaskを使う
from flask import Flask, request, abort

##
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import ImageMessage, MessageEvent, TextMessage, TextSendMessage

##
import requests, json, os, io

from io import BytesIO
from PIL import Image
import numpy as np

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

# LineサーバーにPOSTリクエストが送られた時にアクションを起こすURL（WebhookURL）をcallbackに設定している．
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value．ヘッダーからLineサーバーからの応答であるかを確認する．
    signature = request.headers['X-Line-Signature']

    # get request body as text
    # request body の正体については調査中．
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    # handlerやhandleの役割については調査中．
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# テキストを受け取る部分
@handler.add(MessageEvent, message=TextMessage)
def handler_message(event):
    if event.message.text == "ミカンおくるね":
        text = "おっけい！"
    else:
        text = "ミカンまだかい？"

    #linebotのAPIを使っている．ここでTextSendMessageはpython用のLineBotSDK．
    # 引数であるeventの正体は調査中．
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text))

# 画像を受け取る部分
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    #userが送る各メッセージにはidが振り当てられている．
    message_id = event.message.id

    #getImageLineは下で定義した関数
    result = getImageLine(message_id)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result)
        )

def getImageLine(id):

    # LineServer上で画像が保存される．URLを以下で指定する．
    line_url = 'https://api.line.me/v2/bot/message/' + id + '/content/'

    # 画像のLineserverから取得．requestのgetメソッド（urlとheaderをつける）で実現．
    result = requests.get(line_url, headers=header)
    print(result)

    # 画像の保存.BytesIO()でバイト型に変換している．
    im = Image.open(BytesIO(result.content))
    ##jpgで指定したURLに保存．(このように一時的に使うファイルはtmpに保存する)
    image_url = '/tmp/' + id + '.jpg'
    im.save(image_url)

    #画像URLからPIL(Python Image Library)で画像を読み込む．
    #PILの代わりにOpen-CVを使うことも可能．
    image = Image.open(image_url)
    if image is None:
        print("Not Open..")
    else:
        print("Open Success!!")

    #画像数値処理.#画像中心40pix * 40pixだけ抜いてくる．
    x = np.shape(image)[0]
    y = np.shape(image)[1]
    image_cropped = image.crop(( x/2 - 20, y/2 -20, x/2 + 20, y/2 + 20))

    #RGB値に変換
    r,g,b = image_cropped.split()
    r = np.array(r)
    score = np.average(r)
    if  score > 200:
        result = "このミカンはうまいぞ!"
    else:
        result = "こんなんミカンじゃねえ(怒) "

    #AIを使う時は以下の関数を使う．（まだ重みファイルhoge.h5を作ってないので使えない）
    #result = cnn_model(image_cropped)

    return result

def get_text_by_ms(image_url):
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

def cnn_model(img):
    # グローバル変数を取得する
    global model

    # 一番初めだけ model をロードしたい
    if model is None:
        model = load_model('./hoge.h5')

    # ロードしたモデルをAIで予測
    predict = model.predict(img)
    label=np.argmax(predict)

    if label == 1:
        result = "このミカンは美味いぞ！"
    elif label == 2:
        result = "こんなんみかんじゃねえ（怒）"
    return result

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
