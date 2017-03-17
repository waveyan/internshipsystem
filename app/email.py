# -*- coding: utf-8 -*-
from threading import Thread
from flask import current_app
from flask.ext.mail import Message
from . import mail
from email import charset
charset.add_charset('utf-8', charset.SHORTEST, charset.BASE64, 'utf-8')      #解决邮件不能使用中文问题 


def send_async_email(app,msg):
    with app.app_context():
         mail.send(msg)

def send_email(recipients,body,html):
    app = current_app._get_current_object()
    #msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
    #              sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg = Message('[理工]'+'通知信件',recipients = [recipients],charset='utf-8')       #Message（主题，发件人，收件人，charset='utf-8'（解决邮件不能使用中文问题 ））
    #msg.body = render_template(template + '.txt', **kwargs)
    #msg.html = render_template(template + '.html', **kwargs)
    msg.body = body
    msg.html = html
    #mail.send(msg)
    thr = Thread(target=send_async_email, args=[app,msg])
    #print(body)
    #print(html)
    thr.start()
    #return thr
