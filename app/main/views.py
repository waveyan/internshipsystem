from flask import render_template, url_for, flash, redirect, request
from .form import searchform, comform, internshipForm, dirctTeaForm
from . import main
from ..models import Permission, InternshipInfor, ComInfor, DirctTea, Student
from flask.ext.login import current_user, login_required
from .. import db
from sqlalchemy import func


@main.route('/choose', methods=['GET', 'POST'])
def choose():
    return render_template('_choose.html', Permission=Permission)


@main.route('/search', methods=['GET', 'POST'])
def search():
    form = searchform()
    if form.validate_on_submit():
        print('assa')
    print(form.key.data)
    return render_template('index.html', form=form, Permission=Permission)


@main.route('/students', methods=['GET', 'POST'])
def students():
    form = searchform()
    return render_template('students.html', form=form, Permission=Permission)


@main.route('/studetail', methods=['GET', 'POST'])
def studetail():
    return render_template('studetail.html', Permission=Permission)


@main.route('/stuinfor', methods=['GET', 'POST'])
def stuinfor():
    return render_template('stuinfor.html', Permission=Permission)


@main.route('/journal', methods=['GET', 'POST'])
def journal():
    return render_template('journal.html', Permission=Permission)


@main.route('/summary', methods=['GET', 'POST'])
def summary():
    return render_template('summary.html', Permission=Permission)


@main.route('/score', methods=['GET', 'POST'])
def score():
    return render_template('score.html', Permission=Permission)


@main.route('/statistics', methods=['GET', 'POST'])
def statistics():
    return render_template('statistics.html', Permission=Permission)


# --------------------------------------------------------------------


# 首页
@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', Permission=Permission)


# 学生实习列表
@main.route('/internshipList')
@login_required
def internshipList():
    internshipInfor = InternshipInfor.query.filter_by(stuId=current_user.stuId).first()
    if internshipInfor is None:
        flash('您还没完成实习信息的填写，请完善相关实习信息！')
        return redirect(url_for('.adcominfor'))
    else:
        comInfor = db.session.execute('select DISTINCT * from InternshipInfor i,ComInfor c where i.comId=c.comId')
        print(comInfor)
        return render_template('internshipList.html', comInfor=comInfor,Permission=Permission)


# 学生实习信息
@main.route('/stuinter/<int:id>', methods=['GET'])
@login_required
def stuinter(id):
    student = Student.query.filter_by(stuId=current_user.stuId).first()
    internship = InternshipInfor.query.filter_by(Id=id).first()
    comInfor = ComInfor.query.filter_by(comId=internship.comId).first()
    dirctTea = DirctTea.query.filter_by(stuId=current_user.stuId).all()
    return render_template('stuIntedetail.html', Permission=Permission, comInfor=comInfor,
                               dirctTea=dirctTea, internship=internship, student=student)


# 添加企业信息
@main.route('/adcominfor', methods=['GET', 'POST'])
@login_required
def adcominfor():
    form = comform()
    if form.validate_on_submit():
        try:
            max_comId = getMaxComId()
            if max_comId is None:
                max_comId = 1;
            else:
                max_comId = max_comId + 1
            comInfor = ComInfor(comName=form.comName.data, comBrief=form.comBrief.data, comAddress=form.comAdress.data,
                                comUrl=form.comUrl.data, comMon=form.comMon.data, comContact=form.comContact.data,
                                comProject=form.comProject.data, comStaff=form.comStaff.data,
                                comPhone=form.comPhone.data,
                                comEmail=form.comEmail.data, comFax=form.comFax.data)
            print('true')
            db.session.add(comInfor)
            flash('实习企业信息添加成功！')
            return redirect(url_for('.addInternship', comId=max_comId))
        except Exception as e:
            db.session.rollback()
            print('实习企业信息：', e)
            flash('实习企业信息提交失败，请重试！')
            return redirect(url_for('.adcominfor'))
    return render_template('adcominfor.html', form=form, Permission=Permission)


# 填写学生实习信息
@main.route('/addInternship/<int:comId>', methods=['GET', 'POST'])
@login_required
def addInternship(comId):
    iform = internshipForm()
    form = dirctTeaForm()
    dirctTea = DirctTea()
    i = 0
    j = 0
    try:
        if request.method == 'POST':
            internship = InternshipInfor(task=request.form.get('task'), start=request.form.get('start'),
                                         end=request.form.get('end'), address=request.form.get('adress'),
                                         comId=comId, stuId=current_user.stuId)
            while True:
                i = i + 1
                j = j + 1
                teaValue = request.form.get('teaId%s' % i)
                cteaValue = request.form.get('cteaName%s' % j)
                if teaValue or cteaValue:
                    if teaValue:
                        dirctTea = DirctTea(teaId=teaValue, teaName=request.form.get('teaName%s' % i),
                                            teaDuty=request.form.get('teaDuty%s' % i),
                                            teaPhone=request.form.get('teaPhone%s' % i),
                                            teaEmail=request.form.get('teaEmail%s' % i), stuId=current_user.stuId)
                    if cteaValue:
                        dirctTea.cteaDuty = request.form.get('cteaDuty%s' % j)
                        dirctTea.cteaEmail = request.form.get('cteaEmail%s' % j)
                        dirctTea.cteaName = cteaValue
                        dirctTea.cteaPhone = request.form.get('cteaEmail%s' % j)
                        dirctTea.stuId = current_user.stuId
                    db.session.add(dirctTea)
                    db.session.commit()
                else:
                    break
            db.session.add(internship)
            db.session.commit()
            flash('提交实习信息成功！')
            return redirect(url_for('.stuinter'))
    except Exception as e:
        print("实习信息：", e)
        db.session.rollback
        flash('提交实习信息失败，请重试！')
        return redirect(url_for('.addInternship', comId=comId))
    return render_template('addInternship.html', iform=iform, form=form, Permission=Permission)


# 企业列表
@main.route('/company', methods=['GET'])
@login_required
def company():
    form = searchform()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.filter_by(status=3).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    return render_template('company.html', form=form, Permission=Permission, comInfor=comInfor, pagination=pagination)


# 审核时的企业列表
@main.route('/notchoose', methods=['GET', 'POST'])
def notchoose():
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.filter_by(status=3).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    return render_template('_notchoose.html',
                           Permission=Permission, comInfor=comInfor, pagination=pagination)


# 企业详细信息
@main.route('/cominfor', methods=['GET'])
@login_required
def cominfor():
    id = request.args.get('id')
    com = ComInfor.query.filter_by(comId=id).first()
    return render_template('cominfor.html', Permission=Permission, com=com)


# 实习企业列表
@main.route('/intecompany', methods=['GET'])
def intecompany():
    form = searchform()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.join(InternshipInfor).group_by(
        InternshipInfor.comId).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    return render_template('intecompany.html', form=form, Permission=Permission, pagination=pagination,
                           comInfor=comInfor)


# 查询最大的企业Id
def getMaxComId():
    res = db.session.query(func.max(ComInfor.comId).label('max_comId')).one()
    return res.max_comId
