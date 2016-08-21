from flask import render_template, redirect, url_for, request, flash
from . import auth
from .form import LoginForm
from ..models import Teacher, Student,Permission
from flask.ext.login import login_required, login_user, logout_user


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        teacher = Teacher.query.filter_by(teaId=form.ID.data).first()
        stu = Student.query.filter_by(stuId=form.ID.data).first()
        if teacher is not None and teacher.password == form.password.data:
            login_user(teacher, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        if stu is not None and stu.password == form.password.data:
            login_user(stu, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('账户或密码不正确！')
    return render_template('auth/login.html', form=form, Permission=Permission)


@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('登出成功！')
    return redirect(url_for('main.index'))
