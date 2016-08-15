# -*- coding: utf-8 -*-

from flask import render_template, url_for, flash, redirect, request, session, send_file
from .form import searchForm, comForm, internshipForm, journalForm, stuForm, teaForm, permissionForm, schdirteaForm, \
    comdirteaForm
from . import main
from ..models import Permission, InternshipInfor, ComInfor, SchDirTea, ComDirTea, Student, Journal, Role, Teacher, \
    not_student_login, update_intern_internStatus, update_intern_jourCheck
from flask.ext.login import current_user, login_required
from .. import db
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta, date
import xlwt, xlrd, os, random
from collections import OrderedDict
from werkzeug.utils import secure_filename

# datepicker failed
'''
from flask_wtf import Form

@main.route('/test', methods=['GET','POST'])
def hello_world():
    form = ExampleForm()
    if form.validate_on_submit():
        return form.dt.data.strftime('%Y-%m-%d')
    return render_template('example.html')
'''


# @main.route('/search', methods=['GET', 'POST'])
# def search():
#     form = searchForm()
#     if form.validate_on_submit():
#         print('assa')
#     print(form.key.data)
#     return render_template('index.html', form=form, Permission=Permission)


@main.route('/students', methods=['GET', 'POST'])
def students():
    form = searchForm()
    return render_template('students.html', form=form, Permission=Permission)


# 实习提交表
@main.route('/stuinfor', methods=['GET', 'POST'])
def stuinfor():
    return render_template('stuinfor.html', Permission=Permission)


@main.route('/journal', methods=['GET', 'POST'])
def journal():
    return render_template('journal.html', Permission=Permission)


@main.route('/summary', methods=['GET', 'POST'])
def summary():
    return render_template('summary.html', Permission=Permission)

# 评分表
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


# 个人实习企业列表
@main.route('/stuInternList', methods=['GET', 'POST'])
@login_required
@update_intern_jourCheck
@update_intern_internStatus
def stuInternList():
    page = request.args.get('page', 1, type=int)
    if current_user.roleId == 0:
        stuId = current_user.stuId
        student = Student.query.filter_by(stuId=stuId).first()
        internship = InternshipInfor.query.filter_by(stuId=stuId).all()
        # 让添加实习企业 addcominfor 下一步跳转到 addinternship
        if internship is None:
            flash('您还没完成实习信息的填写，请完善相关实习信息！')
            return redirect(url_for('.addcominfor'))
        else:
            pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
                .add_columns(ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start,
                             InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck) \
                .filter(InternshipInfor.stuId == stuId).order_by(
                func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
            internlist = pagination.items
            return render_template('stuInternList.html', internlist=internlist, Permission=Permission,
                                   internship=internship, student=student, pagination=pagination)
    elif current_user.can(Permission.STU_INTERN_SEARCH):
        pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Student, Student.stuId == InternshipInfor.stuId).outerjoin(Teacher, Teacher.teaId==InternshipInfor.icheckTeaId).outerjoin(SchDirTea, SchDirTea.stuId==InternshipInfor.stuId).outerjoin(ComDirTea, and_(ComDirTea.stuId==InternshipInfor.stuId, ComDirTea.comId==InternshipInfor.comId)) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.address, InternshipInfor.task, Teacher.teaName, InternshipInfor.opinion, InternshipInfor.icheckTime, SchDirTea.steaName, SchDirTea.steaDuty, SchDirTea.steaPhone, SchDirTea.steaEmail, ComDirTea.cteaName, ComDirTea.cteaDuty, ComDirTea.cteaPhone, ComDirTea.cteaEmail) \
        .order_by(func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        # 批量导出实习excel表
        if request.method == "POST" and current_user.can(Permission.STU_INTERN_CHECK) :
            isexport = request.form.get('isexport')
            if isexport:
                return excel_export(excel_export_intern, internlist)
        return render_template('stuInternList.html', internlist=internlist, Permission=Permission,
                               pagination=pagination)
    else:
        flash('非法操作')
        return redirect('/')


# 选择实习企业
@main.route('/selectCom', methods=['GET', 'POST'])
@login_required
def selectCom():
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    return render_template('selectCom.html', form=form, Permission=Permission, comInfor=comInfor, pagination=pagination)


# 添加企业信息
@main.route('/addcominfor', methods=['GET', 'POST'])
@login_required
def addcominfor():
    from_url = request.args.get('from_url')
    form = comForm()
    # if form.validate_on_submit():
    if request.method == "POST":
        max_comId = getMaxComId()
        if max_comId is None:
            max_comId = 1
        else:
            max_comId = max_comId + 1
        try:
            # 如果有企业信息审核权限的用户添加企业信息自动通过审核
            if current_user.can(Permission.COM_INFOR_CHECK):
                comInfor = ComInfor(comName=form.comName.data, comBrief=form.comBrief.data,
                                    comAddress=form.comAddress.data,
                                    comUrl=form.comUrl.data, comMon=form.comMon.data, comContact=form.comContact.data,
                                    comProject=form.comProject.data, comStaff=form.comStaff.data,
                                    comPhone=form.comPhone.data,
                                    comEmail=form.comEmail.data, comFax=form.comFax.data, comCheck=2)
            else:
                comInfor = ComInfor(comName=form.comName.data, comBrief=form.comBrief.data,
                                    comAddress=form.comAddress.data,
                                    comUrl=form.comUrl.data, comMon=form.comMon.data, comContact=form.comContact.data,
                                    comProject=form.comProject.data, comStaff=form.comStaff.data,
                                    comPhone=form.comPhone.data,
                                    comEmail=form.comEmail.data, comFax=form.comFax.data)
            print('true')
            db.session.add(comInfor)
            db.session.commit()
            flash('实习企业信息添加成功！')
            # 若是从 .stuInternList 添加实习信息跳转至此,则现在跳转到 .addinternship,继续完善实习信息添加
            if from_url == "stuInternList":
                return redirect(url_for('.addInternship', comId=max_comId))
            else:
                return redirect(url_for('.interncompany'))
        except Exception as e:
            db.session.rollback()
            print('实习企业信息：', e)
            flash('实习企业信息提交失败，请重试！')
            return redirect(url_for('.addcominfor'))
    return render_template('addcominfor.html', form=form, Permission=Permission, from_url=from_url)


# 添加实习信息
# 只能学生本人添加
@main.route('/addInternship', methods=['GET', 'POST'])
@login_required
def addInternship():
    iform = internshipForm()
    schdirteaform = schdirteaForm()
    comdirteaform = comdirteaForm()
    i = 0
    j = 0
    try:
        if request.method == 'POST':
            # 若请求非学生,从request获取学生学号和姓名
            if current_user.roleId != 0:
                stuId = request.form.get('stuId')
                stuName = request.form.get('stuName')
                # 检查学号姓名是否拼配
                flag = Student.query.filter_by(stuId=stuId, stuName=stuName).count()
                if not flag:
                    flash('添加失败:没有此学生信息')
                    return redirect('/')
            else:
                stuId = current_user.stuId
            comId = request.args.get('comId')
            start = datetime.strptime(request.form.get('start'), '%Y-%m-%d').date()
            end = datetime.strptime(request.form.get('end'), '%Y-%m-%d').date()
            now = datetime.now().date()
            # 比较实习时间与当前时间,判断实习状态
            if start < now :
                if end <= now :
                    internStatus = 2 # 实习结束
                    print ('this is 1')
                if end > now :
                    internStatus = 1 #实习中
                    print ('this is 2')
            elif start > now :
                internStatus = 0 #待实习
                print ('this is 3')
            else:
                internStatus = 1  # start=now, 实习中
                print('this is 4')
            internship = InternshipInfor(
                task=request.form.get('task'),
                start=start,
                end=end,
                time=datetime.now().date(),
                address=request.form.get('address'),
                comId=comId,
                stuId=stuId,
                internStatus=internStatus
            )
            while True:
                i = i + 1
                j = j + 1
                teaValue = request.form.get('teaId%s' % i)
                cteaValue = request.form.get('cteaName%s' % j)
                if teaValue:
                    schdirtea = SchDirTea(
                        teaId=teaValue,
                        stuId=stuId,
                        teaName=request.form.get('teaName%s' % i),
                        teaDuty=request.form.get('teaDuty%s' % i),
                        teaPhone=request.form.get('teaPhone%s' % i),
                        teaEmail=request.form.get('teaEmail%s' % i)
                    )
                    db.session.add(schdirtea)
                if cteaValue:
                    comdirtea = ComDirTea(
                        stuId=stuId,
                        teaName=cteaValue,
                        comId=comId,
                        teaDuty=request.form.get('cteaDuty%s' % j),
                        teaEmail=request.form.get('cteaEmail%s' % j),
                        teaPhone=request.form.get('cteaPhone%s' % j)
                    )
                    db.session.add(comdirtea)
                else:
                    break
            # 先commit internship,更新等等需用到的internId
            try:
                db.session.add(internship)
                db.session.commit()
            except Exception as e:
                print('添加指导老师：', e)
                db.session.rollback()
                flash('添加实习信息失败，请重试！')
                return redirect('/')
            # 若所选企业未被审核通过,且用户有审核权限,自动审核通过企业
            if current_user.can(Permission.COM_INFOR_CHECK):
                try:
                    db.session.execute('update ComInfor set comCheck=2 where comId=%s'% comId)
                except Exception as e:
                    db.session.rollback()
                    print(datetime.now(),'/addinternship 审核企业失败:',e)
                    flash('所选企业审核失败,请重试')
                    return redirect('/')
            # 初始化日志
            internId = int(InternshipInfor.query.order_by(desc(InternshipInfor.Id)).first().Id)
            journal_init(internId)
            # 更新累计实习人数
            cominfor = ComInfor.query.filter_by(comId=comId).first()
            if cominfor.students:
                cominfor.students = int(cominfor.students) + 1
            else:
                cominfor.students = 1
            db.session.add(cominfor)
            db.session.commit()
            flash('提交实习信息成功！')
            return redirect(url_for('.stuInternList'))
    except Exception as e:
        print("实习信息：", e)
        db.session.rollback
        flash('提交实习信息失败，请重试！')
        return redirect(url_for('.addcominfor'))
    return render_template('addinternship.html', iform=iform, schdirteaform=schdirteaform, comdirteaform=comdirteaform,
                           Permission=Permission)


# 学生个人实习信息
@main.route('/xIntern', methods=['GET', 'POST'])
@login_required
def xIntern():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    comId = request.args.get('comId')
    internId = request.args.get('internId')
    student = Student.query.filter_by(stuId=stuId).first()
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    schdirtea = SchDirTea.query.filter_by(stuId=stuId).all()
    comdirtea = ComDirTea.query.filter_by(stuId=stuId, comId=comId).all()
    return render_template('xIntern.html', Permission=Permission, comInfor=comInfor,
                           schdirtea=schdirtea, comdirtea=comdirtea, internship=internship, student=student)


# 审核通过实习信息
@main.route('/xIntern_comfirm', methods=["POST", "GET"])
@not_student_login
def xIntern_comfirm():
    if current_user.can(Permission.STU_INTERN_CHECK):
        internId = request.form.get('internId')
        internCheck = request.form.get('internCheck')
        stuId = request.form.get('stuId')
        opinion = request.form.get('opinion')
        comId = InternshipInfor.query.filter_by(Id=internId).first().comId
        com = ComInfor.query.filter_by(comId=comId).first()
        try:
            if opinion:
                db.session.execute('update InternshipInfor set internCheck=%s, opinion="%s" where Id=%s' % (
                    internCheck, opinion, internId))
            else:
                db.session.execute('update InternshipInfor set internCheck=%s where Id=%s' % (internCheck, internId))
            # 若所选企业未被审核通过,且用户有审核权限,自动审核通过企业
            if com.comCheck != 2 and current_user.can(Permission.COM_INFOR_CHECK):
                db.session.execute('update ComInfor set comCheck=2 where comId=%s'% comId)
        except Exception as e:
            db.session.rollback()
            print(datetime.now(),":", current_user.get_id(), "审核实习申请失败", e)
            flash("实习申请审核失败")
            return redirect("/")
        flash("实习申请审核成功")
    return redirect(url_for('.stuInternList', stuId=stuId))


# 修改实习信息
@main.route('/xInternEdit', methods=['GET', 'POST'])
@login_required
def xInternEdit():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    elif not current_user.can(Permission.STU_INTERN_EDIT):
        flash('非法操作')
        return redirect('/')
    if request.form.get('stuId'):
        stuId = request.form.get('stuId')
        comId = request.form.get('comId')
        internId = request.form.get('internId')
    else:
        stuId = request.args.get('stuId')
        comId = request.args.get('comId')
        internId = request.args.get('internId')
    student = Student.query.filter_by(stuId=stuId).first()
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    schdirtea = SchDirTea.query.filter_by(stuId=stuId).all()
    comdirtea = ComDirTea.query.filter_by(stuId=stuId, comId=comId).all()
    # 各种Form
    stuform = stuForm()
    comform = comForm()
    internform = internshipForm()
    schdirteaform = schdirteaForm()
    comdirteaform = comdirteaForm()
    return render_template('xInternEdit.html', Permission=Permission, comInfor=comInfor, schdirtea=schdirtea, \
                           comdirtea=comdirtea, internship=internship, student=student, stuform=stuform, \
                           comform=comform, \
                           internform=internform, schdirteaform=schdirteaform, comdirteaform=comdirteaform)


# 修改实习信息 个人实习信息--实习岗位信息
@main.route('/xInternEdit_intern', methods=["POST", "GET"])
@login_required
def xInternEdit_intern():
    if current_user.roleId == 0:
        stuId = current_user.stuId
        internCheck = 0
    elif current_user.can(Permission.STU_INTERN_CHECK):
        stuId = request.form.get('stuId')
        internCheck = 2
    task = request.form.get('task')
    address = request.form.get('address')
    start = request.form.get('start')
    end = request.form.get('end')
    time = datetime.now().date()
    comId = request.form.get("comId")
    internId = request.form.get("internId")
    if task is None or address is None or start is None or end is None or time is None or comId is None or stuId is None or internId is None:
        flash("修改实习信息失败,请重试")
        return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))
    db.session.execute(' \
        update InternshipInfor set \
        task = "%s", \
        address = "%s", \
        start = "%s", \
        end = "%s", \
        time = "%s", \
        internCheck = %s \
        where Id=%s' \
        % (task, address, start, end, time, internCheck, internId)
        )
    # 实习信息修改,日志跟随变动
    journal_migrate(internId)
    return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))


# 修改实习信息 个人实习信息--企业指导老师
@main.route('/xInternEdit_comdirtea', methods=["POST"])
@login_required
def xInternEdit_comdirtea():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.form.get('stuId')
    Id = request.form.get("Id")
    comId = request.form.get('comId')
    start = request.form.get('start')
    teaName = request.form.get('cteaName')
    teaDuty = request.form.get('cteaDuty')
    teaPhone = request.form.get('cteaPhone')
    teaEmail = request.form.get('cteaEmail')
    internId = request.form.get("internId")
    print(internId)
    print(stuId)
    if teaName is None or comId is None or internId is None or stuId is None:
        flash("修改实习信息失败,请重试")
        return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))
    db.session.execute(' \
        update ComDirTea set \
        teaName = "%s", \
        teaDuty = "%s", \
        teaPhone ="%s", \
        teaEmail = "%s" \
        where Id=%s'
                       % (teaName, teaDuty, teaPhone, teaEmail, Id)
                       )
    flash("实习信息修改成功")
    return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))


# 修改实习信息 删除整个实习页面
@main.route('/comfirmDeleteJournal_Intern', methods=['POST'])
@login_required
def comfirmDeletreJournal_Intern():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.form.get('stuId')
    internId = request.form.get('internId')
    from_url = request.form.get('from_url')
    try:
        # 企业指导老师,日志,实习一同删除
        comId = InternshipInfor.query.filter_by(Id=internId).first().comId
        db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s' % (stuId, comId))
        db.session.execute('delete from Journal where internId=%s and stuId=%s' % (internId, stuId))
        db.session.execute('delete from InternshipInfor where Id=%s and stuId=%s' % (internId, stuId))
        # 企业累计实习人数减一
        db.session.execute('update ComInfor set students = students -1 where comId=%s' % temp_comId)
        flash('删除日志和实习信息成功')
        if from_url == "/xIntern":
            return redirect(url_for('.stuInternList'))
        if from_url == "/xJournal":
            return redirect(url_for('.stuJournalList'))
    except Exception as e:
        print('删除日志和实习信息失败:', e)
        db.session.rollback
        flash('提交实习信息失败，请重试！')
        if from_url == "/xIntern":
            return redirect(url_for('.stuInternList'))
        elif from_url == "/xJournal":
            return redirect(url_for('.stuJournalList'))
    return redirect('/')


# 企业详细信息,方法POST不可删除，在修改返回时有用
@main.route('/cominfor', methods=['GET', 'POST'])
@login_required
def cominfor():
    id = request.args.get('id')
    com = ComInfor.query.filter_by(comId=id).first()
    return render_template('cominfor.html', Permission=Permission, com=com)


# 实习企业列表
@main.route('/interncompany', methods=['GET', 'POST'])
@login_required
def interncompany():
    form = searchForm()
    city = {}
    page = request.args.get('page', 1, type=int)
    com = create_com_filter(city)
    pagination = com.order_by(ComInfor.comDate.desc()).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    # 批量导出实习excel表
    if request.method == "POST" and current_user.can(Permission.COM_INFOR_CHECK) :
        isexport = request.form.get('isexport')
        if isexport:
            return excel_export(excel_export_com, com.all())
    # 搜索
    if request.method == 'POST':
        return redirect(url_for('.search', key=form.key.data, me='intern'))
    return render_template('interncompany.html', form=form, Permission=Permission, pagination=pagination,
                           comInfor=comInfor, city=city)



# 企业信息用户操作筛选项,对所选筛选项进行清空
@main.route('/update_filter', methods=['GET', 'POST'])
@login_required
def update_filter():
    city = request.args.get('city')
    name = request.args.get('name')
    students = request.args.get('students')
    flag = request.args.get('flag')
    if city is not None:
        session['name'] = None
        session['students'] = None
        session['status'] = None
    elif name is not None:
        session['students'] = None
        session['status'] = None
    elif students is not None:
        session['status'] = None
    else:
        session['city'] = None
        session['name'] = None
        session['students'] = None
        session['status'] = None
    if flag == '1':
        return redirect(url_for('.allcomCheck'))
    elif flag == '0':
        return redirect(url_for('.allcomDelete'))
    else:
        return redirect(url_for('.interncompany'))


# 搜索,只对企业名称存在的关键字作搜索
@main.route('/search/<key>', methods=['GET', 'POST'])
@login_required
def search(key):
    form = searchForm()
    if current_user.can(Permission.COM_INFOR_CHECK):
        if request.args.get('me') == 'intern':
            cominfor = ComInfor.query.all()
            comInfor = []
            num = 0
            for c in cominfor:
                if c.comName.find(key) != -1:
                    comInfor.append(c)
                    num = num + 1
    elif request.args.get('me') == 'intern':
        cominfor = ComInfor.query.filter_by(comCheck=2).all()
        comInfor = []
        num = 0
        for c in cominfor:
            if c.comName.find(key) != -1:
                comInfor.append(c)
                num = num + 1
    return render_template('searchResult.html', num=num, form=form, Permission=Permission, comInfor=comInfor, key=key)


# 填写实习日志
@main.route('/addjournal/<int:comId>', methods=['GET', 'POST'])
@login_required
def addjournal(comId):
    form = journalForm()
    if form.validate_on_submit():
        # workend = datetime.strptime(form.workStart.data, '%Y-%m-%d').date()
        workend = form.workStart.data
        journal = Journal(
            stuId=current_user.stuId,
            workStart=form.workStart.data.strftime('%Y-%m-%d'),
            weekNo=form.weekNo.data,
            workEnd=workend,
            comId=comId,
            mon=form.mon.data,
            tue=form.tue.data,
            wed=form.wed.data,
            thu=form.thu.data,
            fri=form.fri.data,
            sat=form.sat.data,
            sun=form.sun.data)
        db.session.add(journal)
        try:
            db.session.commit()
            flash('提交成功！')
            return redirect(url_for('.myjournal', comId=comId))
        except Exception as e:
            db.session.rollback()
            print('日志提交失败：', e)
            flash('提交失败！')
    return render_template('addjournal.html', Permission=Permission, form=form)


# 管理员\普通教师\审核教师
# 特定企业的实习学生列表
@main.route('/comInternList/<int:comId>', methods=['GET', 'POST'])
@login_required
def studentList(comId):
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    comName = ComInfor.query.filter(ComInfor.comId == comId).with_entities(ComInfor.comName).first()[0]
    # filter过滤当前特定企业ID
    pagination = Student.query.join(InternshipInfor).filter(InternshipInfor.comId == comId).order_by(
        Student.grade).paginate(page, per_page=8, error_out=False)
    student = pagination.items
    for stu in student:
        internStatus = InternshipInfor.query.filter_by(comId=comId, stuId=stu.stuId, internStatus=0).count()
        session[stu.stuId] = internStatus
    return render_template('studentList.html', form=form, pagination=pagination, student=student, Permission=Permission,
                           comId=comId, comName=comName)

# 单条审核企业信息
@main.route('/com_comfirm', methods=['GET', 'POST'])
@not_student_login
def com_comfirm():
    if not current_user.can(Permission.COM_INFOR_CHECK):
        return redirect(url_for('.interncompany'))
    else:
        if request.method == 'POST':
            comId = request.form.get('comId')
            check = request.form.get('comCheck')
            print(check)
            print(comId)
            com = ComInfor.query.filter_by(comId=comId).first()
            if check == 'pass':
                com.comCheck = 2
                str = '审核成功，一条信息审核通过。'
                print(str)
            else:
                com.comCheck = 1
                str = '审核成功，一条信息审核未通过。'
            try:
                db.session.add(com)
                db.session.commit()
                flash(str)
                return redirect(url_for(('.interncompany')))
            except Exception as e:
                print('企业信息单条审核：', e)
                db.session.rollback()
                flash('审核失败，请重试！')
                return redirect(url_for(('.interncompany')))


# 批量审核企业信息
@main.route('/allcomCheck', methods=['GET', 'POST'])
@not_student_login
def allcomCheck():
    if not current_user.can(Permission.COM_INFOR_CHECK):
        flash("非法操作")
        return redirect('.interncompany')
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    city = {}
    com = create_com_filter(city, flag=False)
    pagination = com.order_by(ComInfor.comDate.desc()).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    # 确定企业审核通过
    if request.method == "POST":
        comId = request.form.getlist('approve[]')
        for x in comId:
            db.session.execute("update ComInfor set comCheck=2 where comId = %s" % x)
        return redirect(url_for('.allcomCheck', page=pagination.page))
    return render_template('allcomCheck.html', form=form, Permission=Permission, comInfor=comInfor,
                           pagination=pagination, city=city)


# 单条删除企业信息
@main.route('/com_delete', methods=['GET', 'POST'])
@not_student_login
def com_delete():
    if not current_user.can(Permission.COM_INFOR_CHECK):
        return redirect(url_for('.interncompany'))
    else:
        if request.method == 'POST':
            comId = str(request.form.get('comId'))
            print(comId)
            com = ComInfor.query.filter_by(comId=comId).first()
            if com.students != 0:
                flash('此企业信息存在学生的实习信息，不能删除，如要删除请先删除相关学生实习信息！')
                return redirect(url_for('.interncompany'))
            else:
                try:
                    db.session.execute("delete from ComInfor WHERE comId=%s" % comId)
                    flash("删除成功！")
                    return redirect(url_for(('.interncompany')))
                except Exception as e:
                    print('企业信息单条删除：', e)
                    db.session.rollback()
                    flash('删除失败，请重试！')
                    return redirect(url_for(('.interncompany')))


# 批量删除企业信息
@main.route('/allcomDelete', methods=['GET', 'POST'])
@not_student_login
def allcomDelete():
    if not current_user.can(Permission.COM_INFOR_CHECK):
        return redirect('.interncompany')
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    # flash('只有无人实习的企业,或者实习信息被清空的企业,才能被删除')
    city = {}
    com = create_com_filter(city)
    pagination = com.filter_by(students=0).order_by(ComInfor.comDate.desc()).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    # 确定企业删除
    if request.method == "POST":
        comId = request.form.getlist('approve[]')
        for x in comId:
            db.session.execute("delete from ComInfor where comId = %s" % x)
        return redirect(url_for('.allcomDelete', page=pagination.page))
    return render_template('allcomDelete.html', form=form, Permission=Permission, comInfor=comInfor,
                           pagination=pagination, city=city)


# 修改企业信息
@main.route('/editcominfor', methods=['GET', 'POST'])
@not_student_login
def editcominfor():
    comform = comForm()
    id = request.args.get('comId')
    com = ComInfor.query.filter_by(comId=id).first()
    if request.method == 'POST':
        print(comform.comName.data)
        com.comName = comform.comName.data
        com.comAddress = comform.comAddress.data
        com.comUrl = comform.comUrl.data
        com.comBrief = request.form.get('text')
        com.comProject = comform.comProject.data
        com.comMon = comform.comMon.data
        com.comStaff = comform.comStaff.data
        com.comContact = comform.comContact.data
        com.comPhone = comform.comPhone.data
        com.comEmail = comform.comEmail.data
        com.comFax = comform.comFax.data
        try:
            db.session.add(com)
            db.session.commit()
            flash('修改成功！')
            return redirect(url_for('.cominfor', id=id))
        except Exception as e:
            db.session.rollback()
            flash('修改失败，请重试！')
            return redirect(url_for('.editcominfor', comId=id))
    return render_template('editComInfor.html', Permission=Permission, com=com, comform=comform)


# 批量审核实习信息
@main.route('/stuIntern_allCheck', methods=['GET', 'POST'])
@not_student_login
def stuIntern_allCheck():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Student,
                                                                                                    Student.stuId == InternshipInfor.stuId) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, InternshipInfor.comId,
                     InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck) \
        .filter(InternshipInfor.internCheck != 2).order_by(InternshipInfor.internStatus).paginate(page, per_page=8,
                                                                                                  error_out=False)
    internlist = pagination.items
    # 确定实习审核通过
    if request.method == "POST":
        try:
            internId = request.form.getlist('approve[]')
            for x in internId:
                db.session.execute('update InternshipInfor set internCheck=2 where Id = %s' % x)
                # 若所选企业未被审核通过,且用户有审核权限,自动审核通过企业
                comId = InternshipInfor.query.filter_by(Id=x).first().comId
                com = ComInfor.query.filter_by(comId=comId).first()
                if com.comCheck != 2 and current_user.can(Permission.COM_INFOR_CHECK):
                    db.session.execute('update ComInfor set comCheck=2 where comId=%s'% comId)
        except Exception as e:
            db.session.rollback()
            print(datetime.now(),":", current_user.get_id(), "审核实习申请失败", e)
            flash("实习申请审核失败")
            return redirect("/")
        flash('实习信息审核成功')
        return redirect(url_for('.stuIntern_allCheck', page=pagination.page))
    return render_template('stuIntern_allCheck.html', Permission=Permission, internlist=internlist,
                           pagination=pagination)


# 批量删除实习信息
@main.route('/stuIntern_allDelete', methods=['GET', 'POST'])
@not_student_login
def stuIntern_allDelete():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Student,
                                                                                                    Student.stuId == InternshipInfor.stuId) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, InternshipInfor.comId,
                     InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck) \
        .order_by(InternshipInfor.internCheck, InternshipInfor.internStatus).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定删除实习
    if request.method == "POST":
        internId = request.form.getlist('approve[]')
        for x in internId:
            # 企业指导老师,日志,实习一同删除
            temp_intern = InternshipInfor.query.filter_by(Id=x).first()
            temp_comId = temp_intern.comId
            temp_stuId = temp_intern.stuId
            db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s' % (temp_stuId, temp_comId))
            db.session.execute('delete from Journal where internId=%s' % x)
            db.session.execute('delete from InternshipInfor where Id=%s' % x)
            # 企业累计实习人数减一
            db.session.execute('update ComInfor set students = students -1 where comId=%s' % temp_comId)
        flash('实习信息删除成功')
        return redirect(url_for('.stuIntern_allDelete', page=pagination.page))
    return render_template('stuIntern_allDelete.html', Permission=Permission, internlist=internlist,
                           pagination=pagination)


# 批量审核日志
@main.route('/stuJournal_allCheck', methods=['GET', 'POST'])
@not_student_login
def stuJournal_allCheck():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    now = datetime.now().date()
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Journal,
                                                                                                    InternshipInfor.Id == Journal.internId).join(
        Student, InternshipInfor.stuId == Student.stuId) \
        .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id,
                     InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck, InternshipInfor.jourCheck) \
        .filter(InternshipInfor.internCheck == 2, InternshipInfor.internStatus != 0,
                InternshipInfor.jourCheck == 0).group_by(InternshipInfor.Id).order_by(
        func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定日志审核通过
    if request.method == "POST":
        internId = request.form.getlist('approve[]')
        for x in internId:
            db.session.execute('update InternshipInfor set jourCheck=1 where Id=%s' % x)
            db.session.execute('update Journal set jourCheck=1 where internId=%s and workEnd<"%s"' % (x, now))
        flash('日志审核成功')
        return redirect(url_for('.stuJournal_allCheck', page=pagination.page))
    return render_template('stuJournal_allCheck.html', Permission=Permission, pagination=pagination,
                           internlist=internlist)


# 批量删除日志
@main.route('/stuJournal_allDelete', methods=['GET', 'POST'])
@not_student_login
def stuJournal_allDelete():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    now = datetime.now().date()
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Journal,
                                                                                                    InternshipInfor.Id == Journal.internId).join(
        Student, InternshipInfor.stuId == Student.stuId) \
        .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id,
                     InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck, InternshipInfor.jourCheck) \
        .filter(InternshipInfor.internCheck == 2).group_by(InternshipInfor.Id).order_by(
        func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
    # pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Journal, InternshipInfor.Id==Journal.internId).join(Student, InternshipInfor.stuId==Student.stuId) \
    # .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.jourCheck) \
    # .filter(InternshipInfor.internCheck==2, InternshipInfor.internStatus !=0).group_by(InternshipInfor.Id).order_by(func.field(InternshipInfor.internStatus,1,0,2)).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定删除日志
    if request.method == "POST":
        internId = request.form.getlist('approve[]')
        for x in internId:
            # 企业指导老师,日志,实习一同删除
            temp_intern = InternshipInfor.query.filter_by(Id=x).first()
            temp_comId = temp_intern.comId
            temp_stuId = temp_intern.stuId
            db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s' % (temp_stuId, temp_comId))
            db.session.execute('delete from Journal where internId=%s' % x)
            db.session.execute('delete from InternshipInfor where Id=%s' % x)
            # 企业累计实习人数减一
            db.session.execute('update ComInfor set students = students -1 where comId=%s' % temp_comId)
        flash('日志删除成功')
        return redirect(url_for('.stuJournal_allDelete', page=pagination.page))
    return render_template('stuJournal_allDelete.html', Permission=Permission, pagination=pagination,
                           internlist=internlist)


# 学生日志 -- 包含所有实习学生的列表
@main.route('/stuJournalList', methods=['GET', 'POST'])
@login_required
def stuJournalList():
    page = request.args.get('page', 1, type=int)
    if current_user.roleId == 0:
        stuId = current_user.stuId
        internship = InternshipInfor.query.filter_by(stuId=stuId, internCheck=2).count()
        if internship == 0:
            flash('目前还没有通过审核的实习信息,请完善相关实习信息,或耐心等待审核通过')
            return redirect('/')
        else:
            pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Journal,
                                                                                                            InternshipInfor.Id == Journal.internId).join(
                Student, InternshipInfor.stuId == Student.stuId) \
                .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId,
                             InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end,
                             InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.jourCheck) \
                .filter(InternshipInfor.stuId == stuId, InternshipInfor.internCheck == 2).group_by(
                InternshipInfor.Id).order_by(func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page,
                                                                                                         per_page=8,
                                                                                                         error_out=False)
            internlist = pagination.items
            print(len(internlist))
            for x in internlist:
                print(x.stuName)
            return render_template('stuJournalList.html', internlist=internlist, Permission=Permission,
                                   pagination=pagination)
    elif current_user.can(Permission.STU_JOUR_SEARCH):
        pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Journal,
                                                                                                        InternshipInfor.Id == Journal.internId).join(
            Student, InternshipInfor.stuId == Student.stuId) \
            .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id,
                         InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                         InternshipInfor.internCheck, InternshipInfor.jourCheck) \
            .filter(InternshipInfor.internCheck == 2).group_by(InternshipInfor.Id).order_by(
            func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        return render_template('stuJournalList.html', internlist=internlist, Permission=Permission,
                               pagination=pagination)


# 学生日志 -- 特定学生的日志详情
@main.route('/xJournal', methods=['GET', 'POST'])
@login_required
def xJournal():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    internId = request.args.get('internId')
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    student = Student.query.filter_by(stuId=stuId).first()
    # 获得当前时间对应的页码
    now = datetime.now().date()
    cur_page = Journal.query.filter(Journal.stuId == stuId, Journal.internId == internId, Journal.workStart <= now,
                                    Journal.workEnd >= now).first()
    if cur_page:
        page = request.args.get('page', cur_page.weekNo, type=int)
    else:
        page = request.args.get('page', 1, type=int)

    pagination = Journal.query.filter_by(internId=internId).paginate(page, per_page=1, error_out=False)
    journal = pagination.items
    # journal = Journal.query.filter_by(stuId=stuId, internId=internId).all()
    comInfor = db.session.execute('select * from ComInfor where comId in( \
        select comId from InternshipInfor where Id=%s)' % internId).first()
    if internship.internCheck == 2:
        return render_template('xJournal.html', Permission=Permission, internship=internship, journal=journal,
                               student=student, comInfor=comInfor, pagination=pagination, page=page, now=now)
    else:
        flash("实习申请需审核后,才能查看日志")
        return redirect(url_for('.xJournalList', stuId=stuId))


@main.route('/journal_comfirm', methods=['POST', 'GET'])
@not_student_login
def journal_comfirm():
    # 参数都是为了跳转 /xJournal 做准备
    stuId = request.args.get('stuId')
    jourId = request.args.get('jourId')
    internId = request.args.get('internId')
    if current_user.can(Permission.STU_JOUR_CHECK):
        db.session.execute('update Journal set jourCheck=1 where Id=%s' % jourId)
        # 检查是否需要更新 InternshipInfor.jourCheck
        jourCheck = Journal.query.filter(Journal.internId == internId, Journal.jourCheck == 0,
                                         Journal.workEnd < datetime.now().date()).count()
        if jourCheck == 0:
            db.session.execute('update InternshipInfor set jourCheck=1 where Id=%s' % internId)

        flash("日志审核通过")
        return redirect(url_for('.stuJournalList'))
    else:
        # 非法操作,返回主页
        flash('你没有审核日志的权限')
        return redirect('/')


@main.route('/xJournalEdit', methods=['POST', 'GET'])
@login_required
def xJournalEdit():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    elif current_user.roleId == 3:
        stuId = request.args.get('stuId')
    else:
        flash("非法操作")
        return redirect("/")
    jourId = request.args.get('jourId')
    comId = request.args.get('comId')
    internId = request.args.get('internId')
    jour = Journal.query.filter_by(Id=jourId).first()
    student = Student.query.filter_by(stuId=stuId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    jourform = journalForm()
    return render_template('xJournalEdit.html', Permission=Permission, jour=jour, student=student, comInfor=comInfor,
                           internship=internship, jourform=jourform)


@main.route('/xJournalEditProcess', methods=['POST', 'GET'])
@login_required
def xJournalEditProcess():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    elif current_user.roleId == 3:
        stuId = request.form.get('stuId')
    else:
        flash("非法操作")
        return redirect("/")
    jourId = request.form.get('jourId')
    mon = request.form.get('mon')
    tue = request.form.get('tue')
    wed = request.form.get('wed')
    thu = request.form.get('thu')
    fri = request.form.get('fri')
    sat = request.form.get('sat')
    sun = request.form.get('sun')
    stuId = request.form.get('stuId')
    internId = request.form.get('internId')
    try:
        # where加上stuId,是为了防止学生修改其他学生的日志
        db.session.execute('update Journal set \
            mon = "%s", \
            tue = "%s", \
            wed = "%s", \
            thu = "%s", \
            fri = "%s", \
            sat = "%s", \
            sun = "%s" \
            where Id=%s and stuId="%s"'
                           % (mon, tue, wed, thu, fri, sat, sun, jourId, stuId))
    except Exception as e:
        print(datetime.now(), ": 学号为", stuId, "修改日志失败", e)
        flash("修改日志失败")
        return redirect("/")
    flash("修改日志成功")
    return redirect(url_for('.xJournal', stuId=stuId, internId=internId))



'''
# 学生日志详情
@main.route('/stuJour', methods=['GET'])
@not_student_login
def stuJour():
    comId = request.args.get('comId')
    stuId = request.args.get('stuId')
    student = Student.query.filter_by(stuId=stuId).first()
    com = ComInfor.query.filter_by(comId=comId).first()
    journal = db.session.execute('select * from Journal where stuId=%s and comId=%s' % (stuId, comId))
    return render_template('myjournal.html', Permission=Permission, journal=journal, student=student, com=com)
'''


# -------------管理-----------------------------------------------------------------------------------
# 学生用户列表
@main.route('/stuUserList', methods=['GET', 'POST'])
@login_required
def stuUserList():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    form = searchForm()
    grade = {}
    classes = {}
    major = {}
    stu = create_stu_filter(grade, major, classes)
    page = request.args.get('page', 1, type=int)
    pagination = stu.paginate(page, per_page=8, error_out=False)
    student = pagination.items
    return render_template('stuUserList.html', pagination=pagination, form=form, Permission=Permission, student=student,
                           grade=grade, major=major, classes=classes)


# 学生用户信息的筛选项操作,对所选筛选项进行删除,flag=1批量设置
@main.route('/update_stu_filter', methods=['GET', 'POST'])
@login_required
def update_stu_filter():
    grade = request.args.get('grade')
    major = request.args.get('major')
    classes = request.args.get('classes')
    flag = request.args.get('flag')
    if grade is not None:
        session['major'] = None
        session['classes'] = None
        session['sex'] = None
    elif major is not None:
        session['sex'] = None
        session['classes'] = None
    elif classes is not None:
        session['sex'] = None
    else:
        session['major'] = None
        session['classes'] = None
        session['sex'] = None
        session['grade'] = None
    if flag == '1':
        return redirect(url_for('.allStuSet'))
    elif flag == '0':
        return redirect(url_for('.allStuDelete'))
    else:
        return redirect(url_for('.stuUserList'))


# 添加学生用户
@main.route('/addStudent', methods=['GET', 'POST'])
@login_required
def addStudent():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    stuform = stuForm()
    if stuform.validate_on_submit():
        stu = Student(
            stuName=stuform.stuName.data,
            stuId=stuform.stuId.data,
            sex=stuform.sex.data,
            institutes=stuform.institutes.data,
            major=stuform.major.data,
            classes=stuform.classes.data,
            grade=stuform.grade.data
        )
        db.session.add(stu)
        try:
            db.session.commit()
            flash('添加学生信息成功！')
            return redirect(url_for('.stuUserList'))
        except Exception as e:
            db.session.rollback()
            flash('添加学生信息失败请重试！')
            print('添加学生信息：', e)
            return redirect(url_for('.addStudent'))
    return render_template('addStudent.html', stuform=stuform, Permission=Permission)


# 修改学生用户信息
@main.route('/editStudent', methods=['GET', 'POST'])
@login_required
def editStudent():
    form = stuForm()
    stuId = request.args.get('stuId')
    stu = Student.query.filter_by(stuId=stuId).first()
    if request.method == 'POST':
        try:
            stu.stuId = form.stuId.data
            stu.stuName = form.stuName.data
            stu.sex = request.form.get('sex')
            print(request.form.get('sex'))
            stu.major = form.major.data
            stu.grade = form.grade.data
            stu.classes = form.classes.data
            db.session.add(stu)
            db.session.commit()
            flash('修改成功！')
            return redirect(url_for('.stuUserList'))
        except Exception as e:
            print('修改学生用户信息：', e)
            db.session.rollback()
            flash('修改失败，请重试！')
            return redirect(url_for('.editStudent', stuId=stuId))
    return render_template('editStudent.html', Permission=Permission, form=form, stu=stu)


# 单条删除学生用户信息
@main.route('/student_delete', methods=['GET', 'POST'])
@login_required
def student_delete():
    stuId = request.form.get('stuId')
    stu = Student.query.filter_by(stuId=stuId).first()
    try:
        db.session.delete(stu)
        db.session.commit()
        flash('删除成功')
        return redirect(url_for('.stuUserList'))
    except Exception as e:
        print('单条删除学生用户：', e)
        db.session.rollback()
        flash('删除失败，请重试！')
        return redirect(url_for('.stuUserList'))


# 选择和设置角色
@main.route('/selectRole', methods=['GET', 'POST'])
@login_required
def selectRole():
    roles = Role.query.all()
    stuId = request.args.get('stuId')
    teaId = request.args.get('teaId')
    roleId = request.args.get('roleId')
    name = request.args.get('name')
    if stuId:
        # 与批量审核生成的stuId集合一致
        stu = []
        stu.append(stuId)
        session['stu'] = stu
        print('stu')
    if teaId:
        # 同上
        tea = []
        tea.append(teaId)
        session['tea'] = tea
        print(teaId)
    # 点击选择后发生
    if roleId:
        # 学生
        if session.get('stu'):
            for stuId in session['stu']:
                print(stuId)
                stu = Student.query.filter_by(stuId=stuId).first()
                stu.roleId = roleId
                try:
                    db.session.add(stu)
                    db.session.commit()
                except Exception as e:
                    print('设置学生角色', e)
                    flash('设置角色失败，请重试！')
                    db.session.rollback()
                    return redirect(url_for('.selectRole'))
            flash('设置角色成功！')
            return redirect(url_for('.stuUserList'))
        # 教师
        elif session.get('tea'):
            print('教师啊')
            for teaId in session['tea']:
                tea = Teacher.query.filter_by(teaId=teaId).first()
                tea.roleId = roleId
                try:
                    db.session.add(tea)
                    db.session.commit()
                except Exception as e:
                    print('设置教师角色', e)
                    flash('设置角色失败，请重试！')
                    db.session.rollback()
                    return redirect(url_for('.selectRole'))
            flash('设置角色成功！')
            return redirect(url_for('.teaUserList'))
    return render_template('selectRole.html', Permission=Permission, roles=roles, name=name)


# 学生用户批量设置角色
@main.route('/allStuSet', methods=['GET', 'POST'])
@login_required
def allStuSet():
    form = searchForm()
    if session.get('tea'):
        session['tea'] = None
    grade = {}
    major = {}
    classes = {}
    stu = create_stu_filter(grade, major, classes)
    page = request.args.get('page', 1, type=int)
    pagination = stu.paginate(page, per_page=8, error_out=False)
    student = pagination.items
    # session['stu']存储选中的学生学号
    if session.get('stu') is not None:
        session['stu'] = None
    if request.method == 'POST':
        session['stu'] = request.form.getlist('stu[]')
        tips = '%s位学生用户' % len(session['stu'])
        return redirect(url_for('.selectRole', name=tips))
    return render_template('allStuSet.html', Permission=Permission, form=form, student=student, pagination=pagination,
                           page=page, grade=grade, major=major, classes=classes)


# 批量删除学生用户
@main.route('/allStuDelete', methods=['GET', 'POST'])
@login_required
def allStuDelete():
    form = searchForm()
    grade = {}
    major = {}
    classes = {}
    stu = create_stu_filter(grade, major, classes)
    page = request.args.get('page', 1, type=int)
    pagination = stu.paginate(page, per_page=8, error_out=False)
    student = pagination.items
    if request.method == 'POST':
        for x in request.form.getlist('stu[]'):
            try:
                db.session.execute('delete from Student where stuId=%s' % x)
            except Exception as e:
                db.session.rollback()
                print('批量删除学生用户：', e)
                flash('删除失败，请重试！')
                return redirect(url_for('.allStuDelete'))
        flash('删除成功！')
        return redirect(url_for('.allStuDelete'))
    return render_template('allStuDelete.html', Permission=Permission, form=form, student=student,
                           pagination=pagination,
                           page=page, grade=grade, major=major, classes=classes)


# --------------------------------------------

# 教师用户列表
@main.route('/teaUserList', methods=['GET', 'POST'])
@login_required
def teaUserList():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    form = searchForm()
    # 与student共用一个selectRole先清空session['stu']
    if session.get('stu'):
        session['stu'] = None
    if request.args.get('way'):
        session['way'] = request.args.get('way')
    page = request.args.get('page', 1, type=int)
    if session.get('way') == '1':
        pagination = Teacher.query.order_by(Teacher.teaName.desc()).paginate(page, per_page=8, error_out=False)
    else:
        pagination = Teacher.query.order_by(Teacher.teaName).paginate(page, per_page=8, error_out=False)
    teacher = pagination.items
    for tea in teacher:
        session[tea.teaId] = tea.role.roleName
    return render_template('teaUserList.html', pagination=pagination, form=form, Permission=Permission,
                           teacher=teacher)


# 添加教师用户
@main.route('/addTeacher', methods=['GET', 'POST'])
@login_required
def addTeacher():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    form = teaForm()
    if form.validate_on_submit():
        tea = Teacher(teaName=form.teaName.data, teaId=form.teaId.data, teaSex=form.teaSex.data)
        db.session.add(tea)
        try:
            db.session.commit()
            flash('添加教师信息成功！')
            return redirect(url_for('.teaUserList'))
        except Exception as e:
            db.session.rollback()
            flash('添加教师信息失败请重试！')
            print('添加教师信息：', e)
            return redirect(url_for('.addTeacher'))
    return render_template('addTeacher.html', form=form, Permission=Permission)


# 修改教师用户信息
@main.route('/editTeacher', methods=['GET', 'POST'])
@login_required
def editTeacher():
    form = teaForm()
    teaId = request.args.get('teaId')
    tea = Teacher.query.filter_by(teaId=teaId).first()
    if request.method == 'POST':
        try:
            tea.teaId = form.teaId.data
            tea.teaName = form.teaName.data
            tea.teaSex = request.form.get('sex')
            print(request.form.get('sex'))
            db.session.add(tea)
            db.session.commit()
            flash('修改成功！')
            return redirect(url_for('.teaUserList'))
        except Exception as e:
            print('修改教师用户信息：', e)
            db.session.rollback()
            flash('修改失败，请重试！')
            return redirect(url_for('.editTeacher', teaId=teaId))
    return render_template('editTeacher.html', Permission=Permission, form=form, tea=tea)


# 单条删除教师用户信息
@main.route('/teacher_delete', methods=['GET', 'POST'])
@login_required
def teacher_delete():
    teaId = request.form.get('teaId')
    tea = Teacher.query.filter_by(teaId=teaId).first()
    try:
        db.session.delete(tea)
        db.session.commit()
        flash('删除成功')
        return redirect(url_for('.teaUserList'))
    except Exception as e:
        print('单条删除学生用户：', e)
        db.session.rollback()
        flash('删除失败，请重试！')
        return redirect(url_for('.teaUserList'))


# 教师用户批量设置角色
@main.route('/allTeaSet', methods=['GET', 'POST'])
@login_required
def allTeaSet():
    form = searchForm()
    # 与学生共用一个函数
    if session.get('stu'):
        session['stu'] = None
    if request.args.get('way'):
        session['way'] = request.args.get('way')
    page = request.args.get('page', 1, type=int)
    if session.get('way') == '1':
        pagination = Teacher.query.order_by(Teacher.teaName.desc()).paginate(page, per_page=8, error_out=False)
    else:
        pagination = Teacher.query.order_by(Teacher.teaName).paginate(page, per_page=8, error_out=False)
    page = request.args.get('page', 1, type=int)
    teacher = pagination.items
    # session['tea']存储选中的教师ID
    if session.get('tea') is not None:
        session['tea'] = None
    if request.method == 'POST':
        session['tea'] = request.form.getlist('tea[]')
        tips = '%s位教师用户' % len(session['tea'])
        return redirect(url_for('.selectRole', name=tips))
    return render_template('allTeaSet.html', Permission=Permission, form=form, teacher=teacher,
                           pagination=pagination, page=page)


# 批量删除教师用户
@main.route('/allTeaDelete', methods=['GET', 'POST'])
@login_required
def allTeaDelete():
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    if request.args.get('way'):
        session['way'] = request.args.get('way')
    page = request.args.get('page', 1, type=int)
    if session.get('way') == '1':
        pagination = Teacher.query.order_by(Teacher.teaName.desc()).paginate(page, per_page=8, error_out=False)
    else:
        pagination = Teacher.query.order_by(Teacher.teaName).paginate(page, per_page=8, error_out=False)
    teacher = pagination.items
    if request.method == 'POST':
        for x in request.form.getlist('tea[]'):
            try:
                db.session.execute('delete from Teacher where teaId=%s' % x)
            except Exception as e:
                db.session.rollback()
                print('批量删除教师用户：', e)
                flash('删除失败，请重试！')
                return redirect(url_for('.allTeaDelete'))
        flash('删除成功！')
        return redirect(url_for('.allTeaDelete'))
    return render_template('allTeaDelete.html', Permission=Permission, form=form, teacher=teacher,
                           pagination=pagination, page=page)


# 系统角色列表
@main.route('/roleList', methods=['GET', 'POST'])
@login_required
def roleList():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    pagination = Role.query.order_by(Role.permission).paginate(page, per_page=8, error_out=False)
    role = pagination.items
    return render_template('roleList.html', Permission=Permission, role=role, pagination=pagination)



# 添加角色,靠你们改善这个蠢方法了,\r\n不能换行，导致角色列表里的describe不能显全
@main.route('/addRole', methods=['GET', 'POST'])
@login_required
def addRole():
    form = permissionForm()
    a = 0
    if form.validate_on_submit():
        # 生成角色权限
        if form.COM_INFOR_SEARCH.data:
            print('1')
            a = eval(form.COM_INFOR_SEARCH.description) | a
        if form.COM_INFOR_EDIT.data:
            a = eval(form.COM_INFOR_EDIT.description) | a
            print('2')
        if form.COM_INFOR_CHECK.data:
            a = eval(form.COM_INFOR_CHECK.description) | a
            print('4')
        if form.INTERNSHIP_LIST.data:
            a = eval(form.INTERNSHIP_LIST.description) | a
            print('8')
        if form.STU_INTERN_LIST.data:
            a = eval(form.STU_INTERN_LIST.description) | a
        if form.STU_INTERN_SEARCH.data:
            a = eval(form.STU_INTERN_SEARCH.description) | a
        if form.STU_INTERN_EDIT.data:
            a = eval(form.STU_INTERN_EDIT.description) | a
        if form.STU_INTERN_CHECK.data:
            a = eval(form.STU_INTERN_CHECK.description) | a
        if form.STU_INTERN_EXPORT.data:
            a = eval(form.STU_INTERN_EXPORT.description) | a
        if form.STU_JOUR_SEARCH.data:
            a = eval(form.STU_JOUR_SEARCH.description) | a
        if form.STU_JOUR_EDIT.data:
            a = eval(form.STU_JOUR_EDIT.description) | a
        if form.STU_JOUR_CHECK.data:
            a = eval(form.STU_JOUR_CHECK.description) | a
        if form.STU_JOUR_EXPORT.data:
            a = eval(form.STU_JOUR_EXPORT.description) | a
        if form.STU_SUM_SEARCH.data:
            a = eval(form.STU_SUM_SEARCH.description) | a
        if form.STU_SUM_EDIT.data:
            a = eval(form.STU_SUM_EDIT.description) | a
        if form.STU_SUM_EXPORT.data:
            a = eval(form.STU_SUM_EXPORT.description) | a
        if form.STU_SUM_SCO_CHECK.data:
            a = eval(form.STU_SUM_SCO_CHECK.description) | a
        if form.STU_SCO_SEARCH.data:
            a = eval(form.STU_SCO_SEARCH.description) | a
        if form.STU_SCO_EDIT.data:
            a = eval(form.STU_SCO_EDIT.description) | a
        if form.STU_SCO_EXPORT.data:
            a = eval(form.STU_SCO_EXPORT.description) | a
        if form.ADMIN.data:
            a = eval(form.ADMIN.description) | a
        if form.STU_INTERN_IMPORT.data:
            a = eval(form.STU_INTERN_IMPORT.description) | a
        if form.TEA_INFOR_IMPORT.data:
            a = eval(form.TEA_INFOR_IMPORT.description) | a
        if form.PERMIS_MANAGE.data:
            a = eval(form.PERMIS_MANAGE.description) | a
        per = hex(a)
        print(per)
        # print(per)
        # describe = ''.join(p)
        # print(describe)
        id = getMaxRoleId() + 1
        role = Role(roleName=form.roleName.data, roleDescribe=form.roleDescribe.data, permission=per, roleId=id)
        try:
            db.session.add(role)
            db.session.commit()
            flash('添加系统角色成功！')
            return redirect(url_for('.roleList'))
        except Exception as e:
            flash('添加系统角色失败！请重试。。。')
            print('添加系统角色：', e)
            db.session.rollback()
            return redirect(url_for('.addRole'))
    return render_template('addRole.html', Permission=Permission, form=form)


# 删除角色
@main.route('/role_delete', methods=['GET', 'POST'])
@login_required
def role_delete():
    if request.method == 'POST':
        try:
            db.session.execute('delete from Role where roleId=%s' % request.form.get('roleId'))
            flash('删除成功！')
            return redirect(url_for('.roleList'))
        except Exception as e:
            print('删除角色：', e)
            flash('删除失败，请重试！')
            db.session.rollback()
            return redirect(url_for('.roleList'))


# 编辑角色
@main.route('/editRole', methods=['GET', 'POST'])
@login_required
def editRole():
    form = permissionForm()
    roleId = request.args.get('roleId')
    role = Role.query.filter_by(roleId=roleId).first()
    if request.method == 'POST':
        a = 0
        # 生成角色权限
        if form.COM_INFOR_SEARCH.data:
            print('1')
            a = eval(form.COM_INFOR_SEARCH.description) | a
        if form.COM_INFOR_EDIT.data:
            a = eval(form.COM_INFOR_EDIT.description) | a
            print('2')
        if form.COM_INFOR_CHECK.data:
            a = eval(form.COM_INFOR_CHECK.description) | a
            print('4')
        if form.INTERNSHIP_LIST.data:
            a = eval(form.INTERNSHIP_LIST.description) | a
            print('8')
        if form.STU_INTERN_LIST.data:
            a = eval(form.STU_INTERN_LIST.description) | a
        if form.STU_INTERN_SEARCH.data:
            a = eval(form.STU_INTERN_SEARCH.description) | a
        if form.STU_INTERN_EDIT.data:
            a = eval(form.STU_INTERN_EDIT.description) | a
        if form.STU_INTERN_CHECK.data:
            a = eval(form.STU_INTERN_CHECK.description) | a
        if form.STU_INTERN_EXPORT.data:
            a = eval(form.STU_INTERN_EXPORT.description) | a
        if form.STU_JOUR_SEARCH.data:
            a = eval(form.STU_JOUR_SEARCH.description) | a
        if form.STU_JOUR_EDIT.data:
            a = eval(form.STU_JOUR_EDIT.description) | a
        if form.STU_JOUR_CHECK.data:
            a = eval(form.STU_JOUR_CHECK.description) | a
        if form.STU_JOUR_EXPORT.data:
            a = eval(form.STU_JOUR_EXPORT.description) | a
        if form.STU_SUM_SEARCH.data:
            a = eval(form.STU_SUM_SEARCH.description) | a
        if form.STU_SUM_EDIT.data:
            a = eval(form.STU_SUM_EDIT.description) | a
        if form.STU_SUM_EXPORT.data:
            a = eval(form.STU_SUM_EXPORT.description) | a
        if form.STU_SUM_SCO_CHECK.data:
            a = eval(form.STU_SUM_SCO_CHECK.description) | a
        if form.STU_SCO_SEARCH.data:
            a = eval(form.STU_SCO_SEARCH.description) | a
        if form.STU_SCO_EDIT.data:
            a = eval(form.STU_SCO_EDIT.description) | a
        if form.STU_SCO_EXPORT.data:
            a = eval(form.STU_SCO_EXPORT.description) | a
        if form.ADMIN.data:
            a = eval(form.ADMIN.description) | a
        if form.STU_INTERN_IMPORT.data:
            a = eval(form.STU_INTERN_IMPORT.description) | a
        if form.TEA_INFOR_IMPORT.data:
            a = eval(form.TEA_INFOR_IMPORT.description) | a
        if form.PERMIS_MANAGE.data:
            a = eval(form.PERMIS_MANAGE.description) | a
        per = hex(a)
        role.roleName = form.roleName.data
        role.roleDescribe = request.form.get('roleDescribe')
        role.permission = per
        try:
            db.session.add(role)
            db.session.commit()
            flash('修改成功！')
            return redirect(url_for('.roleList'))
        except Exception as e:
            db.session.rollback()
            flash('修改失败，请重试！')
            print('修改角色', e)
            return redirect(url_for('.editRole', roleId=roleId))
    return render_template('editRole.html', Permission=Permission, role=role, form=form)



# 查询最大的角色Id
def getMaxRoleId():
    res = db.session.query(func.max(Role.roleId).label('max_roleId')).one()
    return res.max_roleId



# 企业信息生成筛选项，组合查询,,更新筛选项，当flag=Ture为企业实习信息的组合查询
# 和批量删除的组合查询功能,False为批量审核的组合查询功能
# 返回的企业信息查询结果com，生成筛选项赋值在字典city中
def create_com_filter(city, flag=True):
    # 更新筛选项
    if request.args.get('city') is not None:
        session['city'] = request.args.get('city')
        print(session['city'])

    if request.args.get('name') is not None:
        session['name'] = request.args.get('name')
        print(session['name'])

    if request.args.get('students') is not None:
        session['students'] = request.args.get('students')
        print(session['students'])

    if request.args.get('status') is not None:
        session['status'] = request.args.get('status')
        print(session['status'])
    i = 0
    # 组合查询 *_*
    try:
        if session.get('city') is not None:
            print('city:', session['city'])
            com = ComInfor.query.filter_by(comAddress=session['city'])

            if session.get('name') is not None:
                if session['name'] == 'desc':
                    com = com.order_by(ComInfor.comName.desc())
                    print('name')
                else:
                    com = com.order_by(ComInfor.comName.asc())
                    print('name')

            if session.get('students') is not None:
                if session['students'] == 'desc':
                    com = com.order_by(ComInfor.students.desc())
                    print('students')
                else:
                    com = com.order_by(ComInfor.students.asc())
                    print('students')

            if session.get('status') is not None:
                if flag:
                    if session['status'] == '2':
                        com = com.filter_by(comCheck=2)
                        print('status')
                    else:
                        com = com.filter(ComInfor.comCheck != 2)
                        print('status')
                else:
                    if session['status'] == '1':
                        com = com.filter_by(comCheck=1)
                        print('status')
                    else:
                        com = com.filter_by(comCheck=0)
                        print('status')
            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                    print('pagination')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
        elif session.get('name') is not None:
            if session['name'] == 'desc':
                com = ComInfor.query.order_by(ComInfor.comName.desc())
            else:
                com = ComInfor.query.order_by(ComInfor.comName.asc())
            if session.get('students') is not None:
                if session['students'] == 'desc':
                    com = com.order_by(ComInfor.students.desc())
                else:
                    com = com.order_by(ComInfor.students.asc())
            if session.get('status') is not None:
                if flag:
                    if session['status'] == '2':
                        com = com.filter_by(comCheck=2)
                    else:
                        com = com.filter(ComInfor.comCheck != 2)
                else:
                    if session['status'] == '1':
                        com = com.filter_by(comCheck=1)
                        print('status')
                    else:
                        com = com.filter_by(comCheck=0)
                        print('status')
            if session.get('city') is not None:
                com = com.filter_by(comAddress=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
        elif session.get('students') is not None:
            if session['students'] == 'desc':
                com = ComInfor.query.order_by(ComInfor.students.desc())
            else:
                com = ComInfor.query.order_by(ComInfor.students.asc())
            if session.get('name') is not None:
                if session['name'] == 'desc':
                    com = com.order_by(ComInfor.comName.desc())
                else:
                    com = com.order_by(ComInfor.comName.asc())
            if session.get('status') is not None:
                if flag:
                    if session['status'] == '2':
                        com = com.filter_by(comCheck=2)
                    else:
                        com = com.filter(ComInfor.comCheck != 2)
                else:
                    if session['status'] == '1':
                        com = com.filter_by(comCheck=1)
                        print('status')
                    else:
                        com = com.filter_by(comCheck=0)
                        print('status')
            if session.get('city') is not None:
                com = com.filter_by(comAddress=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
        elif session.get('status') is not None:
            if flag:
                if session['status'] == '2':
                    com = ComInfor.query.filter_by(comCheck=2)
                else:
                    com = ComInfor.query.filter(ComInfor.comCheck != 2)
            else:
                if session['status'] == '1':
                    com = ComInfor.query.filter_by(comCheck=1)
                    print('status')
                else:
                    com = ComInfor.query.filter_by(comCheck=0)
                    print('status')

            if session.get('name') is not None:
                if session['name'] == 'desc':
                    com = com.order_by(ComInfor.comName.desc())
                else:
                    com = com.order_by(ComInfor.comName.asc())
            if session.get('students') is not None:
                if session['students'] == 'desc':
                    com = com.order_by(ComInfor.students.desc())
                else:
                    com = com.order_by(ComInfor.students.asc())
            if session.get('city') is not None:
                com = com.filter_by(comAddress=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
        else:
            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    com = ComInfor.query.order_by(ComInfor.comDate.desc())
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                    print('hi')
                else:
                    com = ComInfor.query.filter_by(comCheck=2).order_by(ComInfor.comDate.desc())
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
            else:
                com = ComInfor.query.filter(ComInfor.comCheck != 2).order_by(ComInfor.comDate.desc())
                citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck!=2')
        if not flag:
            com = com.filter(ComInfor.comCheck != 2)
            citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck!=2')
    except Exception as e:
        print('组合筛选：', e)
    # 生成筛选项
    for c in citys:
        city[i] = c.comAddress
        i = i + 1
    return com



# 初始化日志
def journal_init(internId):
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    start = internship.start
    end = internship.end
    comId = internship.comId
    stuId = internship.stuId
    # ISO日历
    start_isoyear = start.isocalendar()[0]
    start_isoweek = start.isocalendar()[1]
    end_isoyear = end.isocalendar()[0]
    end_isoweek = end.isocalendar()[1]
    # 考虑到跨年
    if end_isoyear == start_isoyear:
        weeks = end_isoweek - start_isoweek + 1
    else:
        week = 0
        # 第1年至 n-1 年的周数累计
        for x in range(end_isoweek - start_isoweek):
            if x == 0:
                weeks = datetime(start_isoyear,12,31).isocalendar()[1] - start_isoweek + 1
            else:
                weeks = weeks + datetime(start_isoyear+x,12,31).isocalendar()[1]
        # 第 n 年的周数累计
        weeks = weeks + end_isoweek
    try:
        if weeks > 1:
            # 第一周. 因第一天未必是周一,所以需特别处理
            journal = Journal(
                stuId=stuId,
                comId=comId,
                weekNo=1,
                workStart=start,
                workEnd=start + timedelta(days=(7 - start.isoweekday())),
                internId=internId,
                isoyear=start.isocalendar()[0],
                isoweek=start.isocalendar()[1]
            )
            db.session.add(journal)
            start = start + timedelta(days=(7 - start.isoweekday() + 1))
            # 第二周至第 n|(n-1) 周
            for weekNo in range(weeks - 2):
                journal = Journal(
                    stuId=stuId,
                    comId=comId,
                    weekNo=weekNo + 2,
                    workStart=start,
                    workEnd=start + timedelta(days=6),
                    internId=internId,
                    isoyear=start.isocalendar()[0],
                    isoweek=start.isocalendar()[1]
                )
                db.session.add(journal)
                start = start + timedelta(days=7)
            # 如果还有几天凑不成一周
            if end >= start:
                journal = Journal(
                    stuId=stuId,
                    comId=comId,
                    weekNo=weeks,
                    workStart=start,
                    workEnd=end,
                    internId=internId,
                    isoyear=start.isocalendar()[0],
                    isoweek=start.isocalendar()[1]
                )
                db.session.add(journal)
        else:
            # 如果实习时间不满一周
            journal = Journal(
                stuId=stuId,
                comId=comId,
                weekNo=1,
                workStart=start,
                workEnd=end,
                internId=internId,
                isoyear=start.isocalendar()[0],
                isoweek=start.isocalendar()[1]
            )
        db.session.add(journal)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(current_user.get_id(),datetime.now(),"初始化日志失败",e)
        flash('初始化日志失败')
        return redirect('/')
    return 1


# 更改实习信息情况下, 初始化并转移日志
# 不要与 journal_init() 重复使用!!
# 在存在日志数据情况下,修改实习[日志]时间,将转移两次时间段中,重复时间段的日志
# 最后删除旧的实习信息和日志
def journal_migrate(internId):
    try:
        db.session.execute('update Journal set internId=%s where internId=%s'% (-int(internId), internId))
        journal_init(internId)
        db.session.execute('update Journal j1, Journal j2 \
            set j1.mon=j2.mon, j1.tue=j2.tue, j1.wed=j2.wed, j1.thu=j2.thu, j1.fri=j2.fri, j1.sat=j2.sat, j1.sun=j2.sun \
            where j1.internId=%s and j2.internId=%s and j1.isoweek=j2.isoweek and j1.isoyear=j2.isoyear' \
            % (internId, -int(internId)))
        db.session.execute('delete from Journal where internId=%s'% -int(internId))
    except Exception as e:
        db.session.rollback()
        print(current_user.get_id(),datetime.now(),"初始化并转移日志失败",e)
        flash('初始化并转移日志失败')
        return redirect('/')
    return 1


# 学生用户筛选项的生成，组合查询,更新筛选项
# 返回的学生用户信息查询结果stu，筛选项生成在字grade，major，classes中，flag暂未用到
def create_stu_filter(grade, major, classes, flag=True):
    # 更新筛选项
    if request.args.get('grade') is not None:
        session['grade'] = request.args.get('grade')
        print(session['grade'])

    if request.args.get('major') is not None:
        session['major'] = request.args.get('major')
        print(session['major'])

    if request.args.get('classes') is not None:
        session['classes'] = request.args.get('classes')
        print(session['classes'])

    if request.args.get('sex') is not None:
        session['sex'] = request.args.get('sex')
        print(session['sex'])
    i = 0
    j = 0
    k = 0
    # 组合查询 *_*
    try:
        if session.get('grade') is not None:
            print('grade:', session['grade'])
            stu = Student.query.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])

            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])

        elif session.get('major') is not None:
            print('major:', session['major'])
            stu = Student.query.filter_by(major=session['major'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])

            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])

        elif session.get('classes') is not None:
            print('classes:', session['classes'])
            stu = Student.query.filter_by(classes=session['classes'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])

        elif session.get('sex') is not None:
            print('sex:', session['sex'])
            stu = Student.query.filter_by(sex=session['sex'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])

        else:
            stu = Student.query.order_by(Student.grade.asc())

        grades = db.session.execute('select DISTINCT grade from Student')
        majors = db.session.execute('select DISTINCT major from Student')
        classess = db.session.execute('select DISTINCT classes from Student ORDER BY classes')
    except Exception as e:
        print('组合筛选：', e)
    # 生成筛选项
    for g in grades:
        grade[i] = g.grade
        i = i + 1
    for m in majors:
        major[j] = m.major
        j = j + 1
    for c in classess:
        classes[k] = c.classes
        k = k + 1
    return stu


# 查询最大的企业Id
def getMaxComId():
    res = db.session.query(func.max(ComInfor.comId).label('max_comId')).one()
    return res.max_comId


#---------------Excel表格导入导出-----------------------------------------------

# Excel文档列名的模板. 导入和导出
# 实习信息表
excel_export_intern = OrderedDict(( ('stuId','学号'), ('stuName','姓名'), ('comName','企业名称'), ('address','地址'), ('internCheck','审核状态'), ('internStatus','实习状态'), ('start','开始日期'), ('end','结束日期'), ('task','任务'), ('teaName','审核教师'), ('opinion','审核意见'), ('icheckTime','审核时间'), ('steaName','校内指导老师'), ('steaDuty','校内指导老师职务'), ('steaPhone','校内指导老师电话'), ('steaEmail','校内指导老师邮箱'), ('cteaName','企业指导老师' ), ('cteaDuty','企业指导老师职务'), ('cteaPhone','企业指导老师电话'), ('cteaEmail','企业指导老师邮箱')))
excel_import_intern = { '学号':'stuId', '姓名':'stuName', '企业编号':'comId', '地址':'address', '开始日期':'start', '结束日期':'end', '任务':'task', '审核教师':'teaName', '审核意见':'opinion', '审核时间':'icheckTime', '企业指导老师':'cteaName', '企业指导老师职务':'cteaDuty', '企业指导老师电话':'cteaPhone', '企业指导老师邮箱':'cteaEmail' }
# 企业信息表
excel_export_com = OrderedDict(( ('comId','企业编号'), ('comName','企业名称'), ('comBrief','企业简介'), ('comAddress','地址'), ('comUrl','网站'), ('comMon','营业额'), ('comContact','联系人'), ('comDate','录入时间'), ('comProject','企业项目'), ('comStaff','员工人数'), ('comPhone','电话'), ('comEmail','邮箱'), ('comFax','传真'), ('comCheck','审核状态'), ('students','实习学生人数') ))
excel_import_com = { '企业名称':'comName', '企业简介':'comBrief', '地址':'comAddress', '网站':'comUrl', '营业额':'comMon', '联系人':'comContact', '录入时间':'comDate', '企业项目':'comProject', '员工人数':'comStaff', '电话':'comPhone', '邮箱':'comEmail', '传真':'comFax'}


IMPORT_FOLDER = os.path.abspath('file_cache/xls_import')
EXPORT_FOLDER = os.path.abspath('file_cache/xls_export')
# 可加上成果的上传文件格式限制
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



# 导出Excel
def excel_export(template, data):
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet 1')
    # 列名
    for col, colname in zip( range(len(template)), template ):
        ws.write(0, col, template.get(colname))
    # 数据
    for row, xdata in zip( range(len(data)), data):
        for col, colname in zip( range(len(template)), template ):
            # 根据输出到Excel的类型和内容做判断
            if colname in ['internCheck', 'comCheck']:
                if getattr(xdata, colname) == 0:
                    ws.write(row+1, col, '待审核')
                elif getattr(xdata, colname) == 1:
                    ws.write(row+1, col, '被退回修改')
                else:
                    ws.write(row+1, col, '已审核')
            elif colname in ['internStatus']:
                if getattr(xdata, colname) == 0:
                    ws.write(row+1, col, '待实习')
                elif getattr(xdata, colname) == 1:
                    ws.write(row+1, col, '实习中')
                else:
                    ws.write(row+1, col, '实习结束')
            elif colname in ['stuId', 'comMon', 'cteaPhone', 'steaPhone']:
                if getattr(xdata, colname):
                    ws.write(row+1, col, int(getattr(xdata, colname)))
            elif colname in ['start','end', 'task', 'teaName', 'opinion', 'icheckTime', 'comDate']:
                ws.write(row+1, col, str(getattr(xdata, colname)))
            else:
                ws.write(row+1, col, getattr(xdata, colname))
    # 每个模板最多保存100份导出临时文件
    if template == excel_export_intern:
        file_name = 'internlist_%s.xls' % random.randint(1,100)
        file_attachname = '实习信息导出表_%s.xls' % datetime.now().date()
    elif template == excel_export_com:
        file_name = 'comlist.xls_%s' % random.randint(1,100)
        file_attachname = '企业信息导出表_%s.xls' % datetime.now().date()
    wb.save((os.path.join(EXPORT_FOLDER,file_name)))
    # attachment_finaname为下载时,提供的默认文件名
    return send_file(os.path.join(EXPORT_FOLDER, file_name), as_attachment=True, attachment_filename = file_attachname.encode('utf-8') )


# 导入Excel
def excel_import(file,template):
    book = xlrd.open_workbook(file)
    data = []
    for sheet in range(book.nsheets):
        sh = book.sheet_by_index(sheet)
        col_name = []
        for col in range(sh.ncols):
            # 如果template里面没找到对应的key,则为None. 所在列的数据也不会录入
            col_name.append(template.get(sh.cell_value(rowx=0, colx=col)))
        for row in range(sh.nrows-1):
            data_row = {}
            for col in range(sh.ncols):
                if col_name[col]:
                    data_row[col_name[col]] = str(sh.cell_value(rowx=row+1, colx=col))
            data.append(data_row)
    return data


# excel导入页面处理
@main.route('/excel_importpage', methods=['GET', 'POST'])
@not_student_login
def excel_importpage():
    from_url = request.args.get('from_url')
    if from_url == 'stuInternList':
        permission = current_user.can(Permission.STU_INTERN_CHECK)
    elif from_url == 'interncompany':
        permission = current_user.can(Permission.COM_INFOR_CHECK)
    if not permission:
        flash('非法操作')
        return redirect('/')
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect('/')
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect('/')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save( os.path.join(IMPORT_FOLDER, filename))
            # 上传成功,开始导入
            if from_url == "stuInternList":
                internlist = excel_import( os.path.join(IMPORT_FOLDER,filename), excel_import_intern)
                # 判断属性是否齐全
                for x in ['stuId','stuName', 'comId', 'start', 'end']:
                    if x not in internlist[0].keys():
                        flash('导入失败: 部分必需信息缺失,请使用提供的模板来写入数据')
                        print('导入失败: 部分必需信息缺失,请使用提供的模板来写入数据')
                        return redirect('/')
                now = datetime.now().date()
                try:
                    for intern, col in zip(internlist, range(len(internlist)) ):
                        # 判断必需数据是否完整
                        for x in ['stuId','stuName', 'comId', 'start', 'end']:
                            if intern[x] is None:
                                flash('导入失败:第%s行有不完整或格式不对的数据,请修改后再导入' % col+1)
                                print('导入失败:第%s行有不完整或格式不对的数据,请修改后再导入' % col+1)
                                return redirect('/')
                        # 判定日期分隔符是'-'还是'/'
                        start = intern['start']
                        end = intern['end']
                        if len(start.split('-')) == 3:
                            start = datetime.strptime(start, '%Y-%m-%d').date()
                            end = datetime.strptime(end, '%Y-%m-%d').date()
                        elif len(start.split('/')) == 3:
                            start = datetime.strptime(start, '%Y/%m/%d').date()
                            end = datetime.strptime(end, '%Y/%m/%d').date()
                        else:
                            flash('日志格式错误,日志格式应为 "2000-01-01" 或 "2000/01/01" ')
                            print('日志格式错误,日志格式应为 "2000-01-01" 或 "2000/01/01" ')
                            return redirect('/')
                        if now < start:
                            intern['internStatus'] = 0 # 待实习
                        elif now >= start and now <= end:
                            intern['internStatus'] = 1 # 实习中
                        else:
                            intern['internStatus'] = 2 # 实习结束
                        internship = InternshipInfor(
                            # 使Excel生成的保留一位小数数字,变成保留到个位
                            stuId = str(intern['stuId'])[:-2],
                            address = intern['address'],
                            start = intern['start'],
                            end = intern['end'],
                            task = intern['task'],
                            comId = intern['comId'],
                            internStatus = intern['internStatus']
                            # 这里还应该有很多需要添加的
                            )
                        db.session.add(internship)
                    db.session.commit()
                except Exception as e:
                    flash('导入出现异常')
                    print('导入出现异常:', e)
                    db.session.rollback()
                    return redirect('/')
                flash('导入成功')
                return redirect(url_for('.stuInternList'))
            if from_url == 'interncompany':
                comlist = excel_import( os.path.join(IMPORT_FOLDER,filename), excel_import_com)
                # 判断属性是否齐全
                print (comlist[0].keys())
                for x in ['comName', 'comAddress', 'comProject', 'comPhone','comEmail']:
                    if x not in comlist[0].keys():
                        print (x)
                        flash('导入失败: 部分必需信息缺失,请使用提供的模板来写入数据')
                        print('导入失败: 部分必需信息缺失,请使用提供的模板来写入数据')
                        return redirect('/')
                try:
                    for com, col in zip(comlist, range(len(comlist)) ):
                        # 判断必需数据是否完整
                        for x in ['comName', 'comAddress', 'comProject', 'comPhone','comEmail']:
                            if com[x] is None:
                                flash('导入失败:第%s行有不完整或格式不对的数据,请修改后再导入' % col+1)
                                print('导入失败:第%s行有不完整或格式不对的数据,请修改后再导入' % col+1)
                                return redirect('/')
                        cominfor = ComInfor(
                            comName = com['comName'],
                            comBrief = com['comBrief'],
                            comAddress = com['comAddress'],
                            comUrl = com['comUrl'],
                            # 使Excel生成的保留一位小数数字,变成保留到个位
                            comMon = str(com['comMon'])[:-2],
                            comContact = com['comContact'],
                            comProject = com['comProject'],
                            comStaff = com['comStaff'],
                            comPhone = com['comPhone'],
                            comEmail = com['comEmail'],
                            comFax = com['comFax'],
                            comCheck = 2
                            )
                        db.session.add(cominfor)
                    db.session.commit()
                except Exception as e:
                    flash('导入出现异常')
                    print('导入出现异常:', e)
                    db.session.rollback()
                    return redirect('/')
                flash('导入成功')
                return redirect(url_for('.interncompany'))
        else:
            flash('请上传正确的Excel文件( .xls和 .xlsx格式)')
            return redirect('/')
    return render_template('excel_import.html',Permission=Permission)

