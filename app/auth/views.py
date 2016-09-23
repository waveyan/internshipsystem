from flask import render_template, redirect, url_for, request, flash
from . import auth
from .form import LoginForm
from ..models import Teacher, Student,Permission
from flask.ext.login import login_required, login_user, logout_user,session,current_user
from .LoginAction import LoginAction


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # form = LoginForm()
    # if form.validate_on_submit():
    #     teacher = Teacher.query.filter_by(teaId=form.ID.data).first()
    #     stu = Student.query.filter_by(stuId=form.ID.data).first()
    #     if teacher is not None and teacher.password == form.password.data:
    #         login_user(teacher, form.remember_me.data)
    #         return redirect(request.args.get('next') or url_for('main.index'))
        # if stu is not None and stu.password == form.password.data:
        # # 消息提示
        #     message = {}
        #     internCheck = Student.query.filter_by(stuId=form.ID.data).first().internCheck
        #     message[0] = internCheck
        #     jourCheck = Student.query.filter_by(stuId=form.ID.data).first().jourCheck
        #     message[1] = jourCheck
        #     sumCheck = Student.query.filter_by(stuId=form.ID.data).first().sumCheck
        #     message[2] = sumCheck
        #     session['message'] = message
        #     login_user(stu, form.remember_me.data)
        #     return redirect(request.args.get('next') or url_for('main.index'))
        # flash('账户或密码不正确！')
    loginAction = LoginAction()
    params = request.args.items()
    d = {}
    for i,token in params:
        d[i] = token
    if loginAction.service(d.get('token')):
        if current_user.roleId==0:
            #消息提示
            message={}
            message[0]=current_user.internCheck
            message[1]=current_user.jourCheck
            message[2]=current_user.sumCheck
            session['message']=message
        return redirect(request.args.get('next') or url_for('main.index'))


@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('登出成功！')
    # return redirect(url_for('main.index'))
    return redirect('https://cas.dgut.edu.cn/user/logout?service=http://'+os.environ.get('local_ip'))
