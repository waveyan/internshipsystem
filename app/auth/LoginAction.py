import os
import requests
from flask import redirect, session, request, url_for, flash
from flask.ext.login import login_user, logout_user
from ..models import Teacher,Student
from .. import db


class LoginAction(object):
    def __init__(self):
        # 设置应用系统的AppID，每个应用都不同，到网络中心注册
        self._appId = "swss"
        # 中央认证服务器地址配置，登陆账号密码，获取Token
        self._casLoginUrl = "https://cas.dgut.edu.cn/?appid=%s"%self._appId
        self._casCheckTokenUrl = "http://cas-#.dgut.edu.cn/ssoapi/checktoken"
        # fail to use jinja2 pattern to match server_ip
        self._casReloginUrl = "https://cas.dgut.edu.cn/user/logout?service=http://219.222.189.70"
        # 本应用地址
        # self._successUrl = os.environ.get('local_ip')
        # self._successUrl = url_for('auth.lg')
        self._successUrl = url_for('main.index')
        self._improveTeaInforUrl=url_for('main.improveTeaInfor')


    def service(self, token=None):

        # 没有Token，把用户重定向到中央认证登陆页
        if token is None:
            print('there is no token')
            return self._casLoginUrl
            #输入账号密码，获取Token并返回应用
        else:
            print('Login success')
            # 调用中央认证验证token接口，验证Token的有效性
            tokens = token.split('-')
            if len(tokens) < 3:
                return self._casLoginUrl
            else:
                # 取出token 中的casid
                apiUrl = self._casCheckTokenUrl.replace('#', tokens[1])

                userIp = request.remote_addr
                # 开始访问接口，验证token值
                paramStr = {
                    'token': token,
                    'userip': userIp,
                    'appid': self._appId
                }
                print("token:%s, userip:%s" % (token, userIp))
                #到中央验证系统进行兑票
                r = requests.post(apiUrl, data=paramStr)
                # responseData = r.text
                # 解释Json对象
                resultModel = r.json()

                if resultModel.get('Result') == 0:
                    if resultModel['UserGroup'] == 'Student':
                        student=Student.query.filter_by(stuId=resultModel['LoginName']).first()
                        if student:
                            login_user(student)
                            #消息提示
                            message={}
                            internCheck = Student.query.filter_by(stuId=student.stuId).first().internCheck
                            message[0] = internCheck
                            jourCheck = Student.query.filter_by(stuId=student.stuId).first().jourCheck
                            message[1] = jourCheck
                            sumCheck = Student.query.filter_by(stuId=student.stuId).first().sumCheck
                            message[2] = sumCheck
                            session['message'] = message
                            return self._successUrl
                    else:
                        teacher = Teacher.query.filter_by(teaId=resultModel['LoginName']).first()
                        if teacher:
                            login_user(teacher)
                            if teacher.teaEmail and teacher.teaPhone:
                                return self._successUrl
                            else:
                                return self._improveTeaInforUrl
                    flash("此用户信息未录入本系统!")
                    return self._casReloginUrl
                else:
                    # 返回登陆页
                    return self._casLoginUrl
