import json
import os
import requests
from flask import redirect, session, request, url_for
from flask.ext.login import login_user
from ..models import Teacher,Student
from .. import db


class LoginAction(object):
    def __init__(self):
        # 设置应用系统的AppID，每个应用都不同
        self._appId = "hjgl"
        # 中央认证服务器地址配置
        self._casLoginUrl = "https://cas.dgut.edu.cn/?appid=hjgl"
        self._casCheckTokenUrl = "http://cas-#.dgut.edu.cn/ssoapi/checktoken"
        # 本应用地址
        self._successUrl = os.environ.get('local_ip')

    def service(self, token=None):

        # 没有Token，把用户重定向到中央认证登陆页
        if token is None:
            print('没有token')
            return redirect(self._casLoginUrl)
        else:
            # 调用中央认证验证token接口，验证Token的有效性
            tokens = token.split('-')
            if len(tokens) < 3:
                return redirect(self._casLoginUrl)
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
                #到中央验证系统进行兑票
                r = requests.post(apiUrl, data=paramStr)
                responseData = r.text
                # 解释Json对象
                resultModel = json.loads(responseData)

                if resultModel.get('Result', 1) == 0:
                    if resultModel['UserGroup'] == 'Teacher':
                        teacher = Teacher.query.filter_by(teacherId=resultModel['LoginName']).first()
                        if teacher:
                            login_user(teacher)
                    else:
                        student=Student.query.filter_by(stuId=resultModel['LoginName']).first()
                        if student:
                            login_user(student)
                    return True
                    # return redirect(self._successUrl)
                else:
                    # 返回登陆页
                    return redirect(self._casLoginUrl)
