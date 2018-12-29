#!/usr/bin/python
#coding:utf-8

#tensorflow
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf


from flask import Flask, request, abort,render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, FollowEvent, JoinEvent,PostbackEvent,
    TextSendMessage, TemplateSendMessage,
    TextMessage, ImageMessage, ButtonsTemplate,
    PostbackTemplateAction, MessageTemplateAction,PostbackAction,
    URITemplateAction,ImageSendMessage,CarouselTemplate,CarouselColumn,URIAction,
    CameraAction, CameraRollAction,QuickReply, QuickReplyButton,ConfirmTemplate
)



try:
    from urllib.parse import urlparse,parse_qs
except ImportError:
    from urlparse import urlparse,parse_qs



import json

import requests

#交易清單物件
class product_transaction(object):
    """docstring for menu"""
    def __init__(user,do,product,price=None,amount=None):
        user.do=do
        user.product = product
        user.price = price
        user.amount = amount


#tensorflow function
def load_graph(model_file):
  graph = tf.Graph()
  graph_def = tf.GraphDef()

  with open(model_file, "rb") as f:
    graph_def.ParseFromString(f.read())
  with graph.as_default():
    tf.import_graph_def(graph_def)

  return graph

def read_tensor_from_image_file(file_name,
                                input_height=299,
                                input_width=299,
                                input_mean=0,
                                input_std=255):
  input_name = "file_reader"
  output_name = "normalized"
  file_reader = tf.read_file(file_name, input_name)
  if file_name.endswith(".png"):
    image_reader = tf.image.decode_png(
        file_reader, channels=3, name="png_reader")
  elif file_name.endswith(".gif"):
    image_reader = tf.squeeze(
        tf.image.decode_gif(file_reader, name="gif_reader"))
  elif file_name.endswith(".bmp"):
    image_reader = tf.image.decode_bmp(file_reader, name="bmp_reader")
  else:
    image_reader = tf.image.decode_jpeg(
        file_reader, channels=3, name="jpeg_reader")
  float_caster = tf.cast(image_reader, tf.float32)
  dims_expander = tf.expand_dims(float_caster, 0)
  resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
  normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
  sess = tf.Session()
  result = sess.run(normalized)

  return result

def load_labels(label_file):
  label = []
  proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
  for l in proto_as_ascii_lines:
    label.append(l.rstrip())
  return label

#要設定成global的參數
next_menu_id = None
user = None

#自訂參數
transaction_list=["番茄","香蕉","橘子","高麗菜","玉米"]
shop_or_sell =["購買","販售"]
shopping_or_selling = ["shopping","selling"]



secretFile=json.load(open("./line_key",'r'))

app = Flask(__name__)


line_bot_api = LineBotApi(secretFile.get("channel_access_token"))

handler = WebhookHandler(secretFile.get("secret_key"))

server_url = secretFile.get("server_url")

# 啟動server對外接口，使Line能丟消息進來
@app.route("/", methods=['POST'])
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

#製作一個測試用接口
@app.route('/hello',methods=['GET'])
def hello():
    return 'Hello World!!'

@app.route('/quality_introduction',methods=['GET'])
def quality_introduction():
    return render_template('quality_introduction.html')


@handler.add(FollowEvent)
def reply_text_and_get_user_profile(event):

    menu_id = secretFile.get("home_page_id")

    # 取出消息內User的資料
    user_profile = line_bot_api.get_profile(event.source.user_id)
    
    # header要特別註明是json格式
    Header={'Content-Type':'application/json'}
    
    
    # 將菜單綁定在用戶身上
    # 要到Line官方server進行這像工作，這是官方的指定接口
    linkMenuEndpoint='https://api.line.me/v2/bot/user/%s/richmenu/%s' % (user_profile.user_id, menu_id)
    
    # 官方指定的header
    linkMenuRequestHeader={'Content-Type':'image/jpeg','Authorization':'Bearer %s' % secretFile["channel_access_token"]}
    
    # 傳送post method封包進行綁定菜單到用戶上
    lineLinkMenuResponse=requests.post(linkMenuEndpoint,headers=linkMenuRequestHeader)
    #推送訊息給官方Line
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="呀哈囉！\n歡迎使用 果菜on賴！\n現在是v1.0.0版本唷~" ))


@handler.add(PostbackEvent)
def handle_post_message(event):

    global next_menu_id

    # 取出消息內User的資料
    user_profile = line_bot_api.get_profile(event.source.user_id)
    #抓取postback action的data
    data = event.postback.data

    #用query string 解析data
    data=parse_qs(data)

    #換頁用
    if (data['type']==['link']):

        if (data['where']==['home_page']):

            next_menu_id = secretFile.get("home_page_id")

        elif (data['where']==['shopping_page']):

            next_menu_id = secretFile.get("shopping_page_id")

        elif (data['where']==['selling_page']):

            next_menu_id = secretFile.get("selling_page_id")

        elif (data['where']==['query_page']):

            next_menu_id = secretFile.get("query_page_id")

        elif (data['where']==['quality_page']):

            next_menu_id = secretFile.get("quality_page_id")
        # header要特別註明是json格式
        Header={'Content-Type':'application/json'}
        # 將菜單綁定在用戶身上
        # 要到Line官方server進行這像工作，這是官方的指定接口
        linkMenuEndpoint='https://api.line.me/v2/bot/user/%s/richmenu/%s' % (user_profile.user_id, next_menu_id)

        # 官方指定的header
        linkMenuRequestHeader={'Content-Type':'image/jpeg','Authorization':'Bearer %s' % secretFile["channel_access_token"]}

        # 傳送post method封包進行綁定菜單到用戶上
        lineLinkMenuResponse=requests.post(linkMenuEndpoint,headers=linkMenuRequestHeader)

        next_menu_id = None

    #general_功能簡介
    elif (data['type']==['introduction']):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="還沒有簡介啦><")
        )

    #買什麼&賣什麼
    elif (data['type']==['product_menu']):
        if (data['from']==['shopping']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請選擇想購買的商品",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[0], data="type=list&what=0&do=0")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[1], data="type=list&what=1&do=0")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[2], data="type=list&what=2&do=0")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[3], data="type=list&what=3&do=0")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[4], data="type=list&what=4&do=0")
                                        )
                                    ]
                                )
                )
            )
        elif (data['from']==['selling']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請選擇想販售的商品",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[0], data="type=list&what=0&do=1")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[1], data="type=list&what=1&do=1")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[2], data="type=list&what=2&do=1")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[3], data="type=list&what=3&do=1")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[4], data="type=list&what=4&do=1")
                                        )
                                    ]
                                )
                )
            )


    elif (data['type']==['list']):
        answer_text = "您要"+shop_or_sell[int(data['do'][0])]+"的商品是"+transaction_list[int(data['what'][0])]+"？"
        product_confirm = TemplateSendMessage(
            alt_text='Confirm template',
            template=ConfirmTemplate(
                text=answer_text,
                actions=[
                    PostbackAction(
                        label='是',
                        text='是',
                        data='type=confirm&from=yes&do='+data['do'][0]+'&what='+data['what'][0]
                    ),
                    PostbackAction(
                        label='否',
                        text='不是唷~',
                        data='type=confirm&from=no'
                    )
                ]
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            product_confirm
        )

    elif (data['type']==['confirm']):
        if (data['from']==['yes']):
            #建立物件
            global user
            user = product_transaction(do=int(data['do'][0]),product=transaction_list[int(data['what'][0])])

            per_title = "想《"+shop_or_sell[int(data['do'][0])]+"》的"+transaction_list[int(data['what'][0])]+"單價(元/台斤)是？\n"
            amount_title = "想《"+shop_or_sell[int(data['do'][0])]+"》的"+transaction_list[int(data['what'][0])]+"數量(台斤)是？\n"
            type_title = "輸入格式為=> 數字(空白)數字"
            total = per_title+amount_title+type_title
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=total)
            )
        elif (data['from']==['no']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請重新選擇~")
            )

    elif (data['type']==['final_confirm']):
        if (data['from']==['yes']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="交易已收到")
            )
        elif (data['from']==['no']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請重新選擇~")
            )



    #品質鑑定選單
    elif (data['type']==['quality']):
        if (data['do']==['upload_picture']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="使用快捷功能或自行上傳照片",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(action=CameraAction(label="立即拍照")),
                                        QuickReplyButton(action=CameraRollAction(label="上傳照片"))
                                    ]
                                )
                )
            )
        elif (data['do']==['feedback']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="尚未開放反饋唷~")
            )
        #tensorflow
        elif (data['do']==['analyze']):
            file_name = "quality/"+data['picture'][0]+".jpg"
            model_file = "model/output_graph.pb"
            label_file = "model/output_labels.txt"
            input_height = 224
            input_width = 224
            input_mean = 0
            input_std = 255
            input_layer = "Placeholder"
            output_layer = "final_result"

            graph = load_graph(model_file)
            t = read_tensor_from_image_file(
                file_name,
                input_height=input_height,
                input_width=input_width,
                input_mean=input_mean,
                input_std=input_std)

            input_name = "import/" + input_layer
            output_name = "import/" + output_layer
            input_operation = graph.get_operation_by_name(input_name)
            output_operation = graph.get_operation_by_name(output_name)

            with tf.Session(graph=graph) as sess:
              results = sess.run(output_operation.outputs[0], {
                  input_operation.outputs[0]: t
              })
            results = np.squeeze(results)

            top_k = results.argsort()[-5:][::-1]
            labels = load_labels(label_file)

            quality_text = ""
            for i in top_k:
                results[i] = results[i]*100
                results[i] = results[i].item()
                quality_text = quality_text+labels[i]+"的可能性為{0:.2f}%\n".format(results[i])
            quality_text = quality_text.replace("good","好").replace("soso","中間").replace("bad","壞")
            
            line_bot_api.reply_message(
                          event.reply_token,
                          TextSendMessage(text=quality_text)
                      )

    #查詢選單
    elif (data['type']==['query']):
        if (data['do']==['who_am_i']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="on賴也不知道你素隨-////-")
            )
        elif (data['do']==['how_much_i_have']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="on賴覺得你很有錢喔")
            )
        elif (data['do']==['detail']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="明細還沒上線唷~")
            )
    else:
        pass


@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event):
    file_path = "quality/"+event.message.id+".jpg"

    message_content = line_bot_api.get_message_content(event.message.id)
    with open(file_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="選擇要分析的果菜",
                        quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=PostbackAction(label="小番茄", data="type=quality&do=analyze&picture="+event.message.id)
                                        )
                                    ]
                        )
        )
    )



@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        #用於買賣訂單
        get_text = event.message.text
        get_list = get_text.split()
        if ( type(int(get_list[0]))==int and type(int(get_list[1]))==int):

            if user.price == None:
                user.price=int(get_list[0])
            if user.amount == None:
                user.amount=int(get_list[1])

            check_text = "《"+shop_or_sell[user.do]+"》的商品是《"+user.product+"》\n"\
                            +"《單價》為"+str(user.price)+"(元/台斤)\n"+"《數量》為"+str(user.amount)+"(台斤)"
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://images.pexels.com/photos/533360/pexels-photo-533360.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940',
                        title='確認交易資訊',
                        text=check_text,
                        actions=[
                            PostbackAction(
                                label='確認無誤',
                                text='確認送出',
                                data='type=final_confirm&from=yes&do='+str(user.do)+\
                                    '&product='+user.product+'&price='+str(user.price)+'&amount='+str(user.amount)
                            ),
                            PostbackAction(
                                label='不對，我有問題',
                                text='我有異議！',
                                data='type=finl_confirm&from=no'
                            )
                        ]
                    )
                )
            )
    except ValueError:
        pass


if __name__ == "__main__":
    app.run()