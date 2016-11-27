from flask import render_template, redirect, url_for, request, flash
from . import auth
from .form import LoginForm
from ..models import Teacher, Student,Permission
from flask.ext.login import login_required, login_user, logout_user,session,current_user
from .LoginAction import LoginAction
import os

f = os.popen('ifconfig em1 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1')
server_ip = f.read().strip('\n')
if not server_ip:
    f = os.popen('ifconfig eth0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1')
    server_ip = f.read()
# server_ip = server_ip + ':5000'
logout_url = 'https://cas.dgut.edu.cn/user/logout?service=http://%s' % server_ip


@auth.route('/login', methods=['GET', 'POST'])
def login():
    loginAction = LoginAction()
    params = request.args.items()
    d = {}
    for i,token in params:
        d[i] = token
    redirect_link = loginAction.service(d.get('token'))
    session['isLogout'] = False
    return redirect(redirect_link)

    # # DEBUG
    # teacher = Teacher.query.filter_by(teaId='20149062').first()
    # login_user(teacher)
    # return redirect(url_for('main.index'))



@auth.route('lg',methods=['GET','POST'])
def lg():
    if not current_user.is_authenticated:
        flash('此用户信息暂未录入本系统！')
        return render_template('index.html',Permission=Permission)
    else:
        return redirect(url_for('main.index'))

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    # session['LoginName'] = ''
    # session['UserGroup'] = ''
    # flash('登出成功！')
    #return redirect(url_for('main.index'))
    # return redirect('https://cas.dgut.edu.cn/user/logout?service=http://%s' % server_ip)
    return redirect(url_for('main.index', isLogout=1))
