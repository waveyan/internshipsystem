from flask import g,request
from ..models import Teacher, AnonymousUser
from . import api
from .errors import forbidden
from hashlib import md5
from .. import Config


@api.before_request
def before_request():
    '''对于api的蓝本中，每一个请求都要进行验证key'''
    key=md5(Config.API_KEY.encode('utf-8')).hexdigest()
    if request.url.split('/')[-1].split('?')[0]!=key:
        return forbidden('the key is not valid!')
