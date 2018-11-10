# encoding: utf-8
from flask import Flask, render_template, redirect, url_for, flash, session, request
from wxpy import *
from functools import wraps
import os
import requests
import json
import platform
from pyecharts import Bar
from pyecharts_javascripthon.api import TRANSLATOR
import random

operate_system = platform.system()  # Windows, Linux, Darwin

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)

bot = None
current_user_data = {}

# 自动回复
auto_reply_status = u'已关闭'
auto_reply_content = ''
auto_reply_person = ''
# 撤销监控
msg_watch_status = u'已关闭'
# 远程关机
rshutdown_status = u'已关闭'
# 节假日提醒
festival_msg = u'已关闭'

REMOTE_HOST = "https://pyecharts.github.io/assets/js"
def has_logined(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if bot is None:
            return redirect(url_for('login'))
        if not bot.alive:
            return render_template('blank-page.html', content=u'您已退出登陆了！', msg_watch_status=msg_watch_status,
                                   rshutdown_status=rshutdown_status,
                                   festival_msg=festival_msg)
        if bot.alive:
            return func(*args, **kwargs)

    return wrapper


def chatbot(msg):
    '''
    图灵机器人回复
    :param msg:
    :return:
    '''
    url = 'http://openapi.tuling123.com/openapi/api/v2'
    payload = {
        "reqType": 0,
        "perception": {
            "inputText": {
                "text": msg.text
            },
            "inputImage": {
                "url": "imageUrl"
            },
            "selfInfo": {
                "location": {
                    "city": u"北京",
                    "province": u"北京",
                    "street": u"信息路"
                }
            }
        },
        "userInfo": {
            "apiKey": "574195551ecc430f891ccf20bcb74d6a",
            "userId": msg.chat.puid
        }
    }
    r = requests.post(url, data=json.dumps(payload))

    return r.json()['results'][0]['values']['text']


def register_msg():
    if bot is not None and bot.alive:
        @bot.register(except_self=False, run_async=True, enabled=True)
        def accept_all_msg(msg):
            # 开启备份消息

            # shell功能
            if msg.chat == bot.file_helper and msg.text.strip() == 'aboutme':
                return bot.friends().stats_text()

            # 远程关机逻辑
            if rshutdown_status == u'已开启':
                if msg.chat == bot.file_helper and msg.text.strip() == 'shutdown':
                    try:
                        if operate_system == 'Linux' or operate_system == 'Darwin':
                            os.system('echo u"即将自动关机..."')
                            os.system('shutdown -h now')
                        else:
                            os.system('echo u"即将自动关机..."')
                            os.system('shutdown -s -t 00')
                    except:
                        return u'远程关机失败，请使用root/Administrator权限运行微信辅助系统！'

            # 自动回复逻辑
            if auto_reply_status == u'已开启':
                if auto_reply_content != u'@机器人回复':
                    if auto_reply_person == '':
                        return auto_reply_content
                    elif auto_reply_person == msg.chat.name:
                        return auto_reply_content
                    else:
                        return
                else:
                    # 机器人回复
                    if auto_reply_person == '':
                        return chatbot(msg)
                    elif auto_reply_person == msg.chat.name:
                        return chatbot(msg)
                    else:
                        return
            else:
                return
    else:
        return


@app.errorhandler(404)
def error404_handler(error):
    return render_template('404.html', msg_watch_status=msg_watch_status, rshutdown_status=rshutdown_status,
                           festival_msg=festival_msg), 404


@app.errorhandler(500)
def error500_handler(error):
    return render_template('500.html', msg_watch_status=msg_watch_status, rshutdown_status=rshutdown_status,
                           festival_msg=festival_msg), 500


@app.route('/recently')
@has_logined
def recently():
    cs = bot.chats()
    fs = []
    gs = []
    ms = []
    for i in cs:
        if isinstance(i, Friend):
            fs.append(i)
        elif isinstance(i, Group):
            gs.append(i)
        elif isinstance(i, MP):
            ms.append(i)
    recently_friends = []
    num = 0
    for f in fs:
        num += 1
        tmp = {}
        tmp['username'] = f.name
        tmp['city'] = f.city
        tmp['sex'] = u'男' if f.sex == 1 else u'女'
        tmp['number'] = num
        recently_friends.append(tmp)

    recently_mps = []
    num = 0
    for m in ms:
        tmp = {}
        num += 1
        tmp['mpname'] = m.name
        tmp['signature'] = m.signature
        tmp['number'] = num
        recently_mps.append(tmp)

    recently_groups = []
    num = 0
    for g in gs:
        tmp = {}
        num += 1
        tmp['groupname'] = g.name
        tmp['owner'] = g.owner.name
        tmp['members'] = len(g.members)
        tmp['number'] = num
        recently_groups.append(tmp)

    return render_template('recently.html', recently_friends=recently_friends, recently_groups=recently_groups,
                           recently_mps=recently_mps, msg_watch_status=msg_watch_status,
                           rshutdown_status=rshutdown_status,
                           festival_msg=festival_msg)


@app.route('/all')
@has_logined
def all():
    fs = bot.friends()
    gs = bot.groups()
    ms = bot.mps()

    all_friends = []
    num = 0
    for f in fs:
        num += 1
        tmp = {}
        tmp['username'] = f.name
        tmp['city'] = f.city
        tmp['sex'] = u'男' if f.sex == 1 else u'女'
        tmp['number'] = num
        all_friends.append(tmp)

    all_mps = []
    num = 0
    for m in ms:
        tmp = {}
        num += 1
        tmp['mpname'] = m.name
        tmp['signature'] = m.signature
        tmp['number'] = num
        all_mps.append(tmp)

    all_groups = []
    num = 0
    for g in gs:
        tmp = {}
        num += 1
        tmp['groupname'] = g.name
        tmp['owner'] = g.owner.name
        tmp['members'] = len(g.members)
        tmp['number'] = num
        all_groups.append(tmp)
    return render_template('all.html', all_friends=all_friends, all_groups=all_groups, all_mps=all_mps,
                           msg_watch_status=msg_watch_status,
                           rshutdown_status=rshutdown_status,
                           festival_msg=festival_msg)


@app.route('/auto_reply', methods=['GET', 'POST'])
def auto_reply():
    global auto_reply_status
    global auto_reply_content
    global auto_reply_person
    if request.method == 'GET':
        status = session.get('auto_reply_status', u'已关闭')
        content = session.get('auto_reply_content', "")
        person = session.get('auto_reply_person', "")
        return render_template('auto_reply.html', auto_reply_status=status,
                               auto_reply_content=content, auto_reply_person=person, msg_watch_status=msg_watch_status,
                               rshutdown_status=rshutdown_status, festival_ms=festival_msg)
    else:
        content = request.form.get('auto_reply_content')
        if content == '':
            session['auto_reply_status'] = u'已关闭'
            auto_reply_status = u'已关闭'
        else:
            session['auto_reply_status'] = u'已开启'
            auto_reply_status = u'已开启'
        session['auto_reply_content'] = content
        auto_reply_content = content
        person = request.form.get('auto_reply_person')
        auto_reply_person = person
        session['auto_reply_person'] = person
        return render_template('auto_reply.html', auto_reply_status=auto_reply_status,
                               auto_reply_content=content, auto_reply_person=person, msg_watch_status=msg_watch_status,
                               rshutdown_status=rshutdown_status, festival_msg=festival_msg)


@app.route('/watch')
def msg_watch():
    global msg_watch_status
    if msg_watch_status == u'已关闭':
        msg_watch_status = u'已开启'
    else:
        msg_watch_status = u'已关闭'
    return render_template('msg_watch.html', msg_watch_status=msg_watch_status, rshutdown_status=rshutdown_status,
                           festival_msg=festival_msg)


@app.route('/rshutdown')
def remote_shutdown():
    global rshutdown_status
    if rshutdown_status == u'已关闭':
        rshutdown_status = u'已开启'
    else:
        rshutdown_status = u'已关闭'
    return render_template('remote_shutdown.html', rshutdown_status=rshutdown_status, msg_watch_status=msg_watch_status,
                           festival_msg=festival_msg)


@app.route('/persons_reply', methods=['GET', 'POST'])
def persons_reply():
    '''
    单/群发
    可定时发送
    '''
    if request.method == 'POST':
        usernames = request.form.getlist('username')

        groupnames = request.form.getlist("groupname")

        names = usernames + groupnames
        namestr = '@'
        if names is not None and len(names) != 0:
            namestr = namestr + '@'.join(names)
        else:
            namestr = ''
        return render_template('reply.html', names=namestr, msg_watch_status=msg_watch_status,
                               rshutdown_status=rshutdown_status,
                               festival_msg=festival_msg)
    else:
        return render_template('reply.html', names='', msg_watch_status=msg_watch_status,
                               rshutdown_status=rshutdown_status,
                               festival_msg=festival_msg)


@app.route('/super_reply', methods=['POST'])
def super_reply():
    namestr = request.form.get('namestr')
    timestr = request.form.get('timestr')
    contentstr = request.form.get('contentstr')

    tonames = namestr.split('@')
    time = namestr.split(',')

    response_content = ''
    if contentstr is None or contentstr == '':
        response_content = u'不能发送空内容！'
        return render_template('send_status.html', content=response_content, msg_watch_status=msg_watch_status,
                               rshutdown_status=rshutdown_status,
                               festival_msg=festival_msg)
    for name in tonames:
        try:
            ensure_one(bot.chats().search(name)).send(contentstr)
        except:
            pass
    response_content = u'发送成功！'
    return render_template('send_status.html', content=u'发送成功！', msg_watch_status=msg_watch_status,
                           rshutdown_status=rshutdown_status,
                           festival_msg=festival_msg)


@app.route('/festival_msg')
def festival_msg():
    global festival_msg
    if festival_msg == u'已关闭':
        festival_msg = u'已开启'
    else:
        festival_msg = u'已关闭'
    return render_template('festival_msg.html', festival_msg=festival_msg, msg_watch_status=msg_watch_status,
                           rshutdown_status=rshutdown_status)


@app.route('/login')
def login():
    global bot
    if bot is not None and bot.alive:
        return redirect(url_for('index'))
    try:
        bot = Bot(cache_path=True)
    except:
        bot = Bot(cache_path=True)

    bot.enable_puid()
    try:
        with open("./static/images/current_user.jpg") as p:
            pass
    except:
        bot.self.get_avatar('./static/images/current_user.jpg')
    friends = bot.friends()
    total_friends = len(friends)
    mps = len(bot.mps())
    groups = len(bot.groups())
    boys = 0
    girls = 0
    for f in friends:
        if f.sex == 0:
            girls += 1
        else:
            boys += 1
    current_user_data['name'] = bot.self.name
    current_user_data['wxid'] = bot.self.wxid
    session['name'] = bot.self.name
    session['wxid'] = bot.self.wxid
    current_user_data['signature'] = bot.self.signature
    current_user_data['total_friends'] = total_friends
    current_user_data['boys'] = boys
    current_user_data['girls'] = girls
    current_user_data['groups'] = groups
    current_user_data['mps'] = mps
    # 注册监听全部消息
    register_msg()
    return redirect(url_for('index'))


@app.route('/index')
def index():
    if bot is not None and bot.alive:

        sd = bot.friends().stats_text()

        attr = []
        v1 = []
        for i in sd.split('\n')[6:16]:
            r = i.replace('(0.00%)', '').strip().split(':')
            attr.append(r[0].strip())
            v1.append(int(r[1].strip()))

        attr2 = []
        v2 = []

        for j in sd.split('\n')[19:28]:
            r = j.replace('(0.00%)', '').strip().split(':')
            attr2.append(r[0].strip())
            v2.append(int(r[1].strip()))

        bar = Bar("TOP 10 省份")
        bar.add("省份", attr, v1, is_stack=True)

        bar2 = Bar("TOP 10 城市")
        bar2.add("城市", attr2, v2, is_stack=True)

        return render_template('index.html',
                               myechart=bar.render_embed(),
                               myechart2=bar2.render_embed(),
                               host=REMOTE_HOST,
                               script_list=bar.get_js_dependencies(),
                               script_list2=bar2.get_js_dependencies(),
                               msg_watch_status=msg_watch_status, rshutdown_status=rshutdown_status,
                               festival_msg=festival_msg, **current_user_data)
    else:
        return render_template('blank-page.html', content=u'您还没有登陆！', msg_watch_status=msg_watch_status,
                               rshutdown_status=rshutdown_status,
                               festival_msg=festival_msg)


@app.route('/')
def hello_world():
    return redirect(url_for('index'))


@app.route('/wx_logout')
def wx_logout():
    try:
        bot.logout()
    except:
        pass
    session.clear()
    global msg_watch_status
    global rshutdown_status
    global festival_msg
    msg_watch_status = u'已关闭'
    rshutdown_status = u'已关闭'
    festival_msg = u'已关闭'
    return render_template('logout.html', msg_watch_status=msg_watch_status, rshutdown_status=rshutdown_status,
                           festival_msg=festival_msg)


if __name__ == '__main__':
    app.run(debug=True)
