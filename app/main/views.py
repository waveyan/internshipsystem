from flask import render_template, url_for, flash, redirect, request, session
from .form import searchform, comform, internshipForm, dirctTeaForm, journalForm, stuForm, teaForm, permissionForm
from . import main
from ..models import Permission, InternshipInfor, ComInfor, DirctTea, Student, Journal, Role, Teacher
from flask.ext.login import current_user, login_required
from .. import db
from sqlalchemy import func
import datetime


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


# 个人实习企业列表
@main.route('/myInternList')
@login_required
def myInternList():
    internshipInfor = InternshipInfor.query.filter_by(stuId=current_user.stuId).first()
    if internshipInfor is None:
        flash('您还没完成实习信息的填写，请完善相关实习信息！')
        return redirect(url_for('.addcominfor'))
    else:
        comInfor = db.session.execute(
            'select DISTINCT * from InternshipInfor i,ComInfor c where i.comId=c.comId'
            ' and i.stuId=%s order BY i.internStatus  ' % current_user.stuId)
        return render_template('myInternList.html', comInfor=comInfor, Permission=Permission)


# 选择实习企业
@main.route('/selectCom', methods=['GET', 'POST'])
@login_required
def selectCom():
    form = searchform()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.filter_by(comCheck=2).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    return render_template('selectCom.html', form=form, Permission=Permission, comInfor=comInfor, pagination=pagination)


# 添加企业信息
@main.route('/addcominfor', methods=['GET', 'POST'])
@login_required
def addcominfor():
    form = comform()
    if form.validate_on_submit():
        max_comId = getMaxComId()
        if max_comId is None:
            max_comId = 1;
        else:
            max_comId = max_comId + 1
        try:
            # 如果有企业信息审核权限的用户添加企业信息自动通过审核
            if current_user.can(Permission.COM_INFOR_CHECK):
                comInfor = ComInfor(comName=form.comName.data, comBrief=form.comBrief.data,
                                    comAddress=form.comAdress.data,
                                    comUrl=form.comUrl.data, comMon=form.comMon.data, comContact=form.comContact.data,
                                    comProject=form.comProject.data, comStaff=form.comStaff.data,
                                    comPhone=form.comPhone.data,
                                    comEmail=form.comEmail.data, comFax=form.comFax.data, comCheck=2)
            else:
                comInfor = ComInfor(comName=form.comName.data, comBrief=form.comBrief.data,
                                    comAddress=form.comAdress.data,
                                    comUrl=form.comUrl.data, comMon=form.comMon.data, comContact=form.comContact.data,
                                    comProject=form.comProject.data, comStaff=form.comStaff.data,
                                    comPhone=form.comPhone.data,
                                    comEmail=form.comEmail.data, comFax=form.comFax.data)
            print('true')
            db.session.add(comInfor)
            db.session.commit()
            flash('实习企业信息添加成功！')
            if current_user.roleId == 0:
                return redirect(url_for('.addInternship', comId=max_comId))
            else:
                return redirect(url_for('.interncompany'))
        except Exception as e:
            db.session.rollback()
            print('实习企业信息：', e)
            flash('实习企业信息提交失败，请重试！')
            return redirect(url_for('.addcominfor'))
    return render_template('addcominfor.html', form=form, Permission=Permission)  # 填写学生实习信息


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
            end = datetime.datetime.strptime(request.form.get('end'), '%Y-%m-%d').date()
            now = datetime.datetime.now().date()
            if end > now:
                internStatus = 0
            else:
                internStatus = 1
            internship = InternshipInfor(task=request.form.get('task'), start=request.form.get('start'),
                                         end=request.form.get('end'), address=request.form.get('adress'),
                                         comId=comId, stuId=current_user.stuId, internStatus=internStatus)
            while True:
                i = i + 1
                j = j + 1
                teaValue = request.form.get('teaId%s' % i)
                cteaValue = request.form.get('cteaName%s' % j)
                if teaValue or cteaValue:
                    if teaValue:
                        dirctTea = DirctTea(comId=comId, teaId=teaValue, teaName=request.form.get('teaName%s' % i),
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
            # 更新累计实习人数
            cominfor = ComInfor.query.filter_by(comId=comId).first()
            if cominfor.students:
                cominfor.students = int(cominfor.students) + 1
            else:
                cominfor.students = 1
            db.session.add(cominfor)
            db.session.commit()
            flash('提交实习信息成功！')
            return redirect(url_for('.internshipList'))
    except Exception as e:
        print("实习信息：", e)
        db.session.rollback
        flash('提交实习信息失败，请重试！')
        return redirect(url_for('.addInternship', comId=comId))
    return render_template('addinternship.html', iform=iform, form=form, Permission=Permission)


# 学生个人实习信息,id为企业id
@main.route('/stuinter/<int:id>', methods=['GET'])
@login_required
def stuinter(id):
    student = Student.query.filter_by(stuId=current_user.stuId).first()
    internship = InternshipInfor.query.filter_by(Id=id).first()
    comInfor = ComInfor.query.filter_by(comId=internship.comId).first()
    dirctTea = DirctTea.query.filter_by(stuId=current_user.stuId, comId=internship.comId).all()
    return render_template('stuInten.html', Permission=Permission, comInfor=comInfor,
                           dirctTea=dirctTea, internship=internship, student=student)


# 企业详细信息
@main.route('/cominfor', methods=['GET'])
@login_required
def cominfor():
    id = request.args.get('id')
    com = ComInfor.query.filter_by(comId=id).first()
    return render_template('cominfor.html', Permission=Permission, com=com)


# 实习企业列表
@main.route('/interncompany', methods=['GET', 'POST'])
@login_required
def interncompany():
    form = searchform()
    page = request.args.get('page', 1, type=int)
    if current_user.can(Permission.COM_INFOR_CHECK):
        pagination = ComInfor.query.order_by(ComInfor.comDate).paginate(page, per_page=8, error_out=False)
    else:
        pagination = ComInfor.query.filter_by(comCheck=3).order_by(ComInfor.students.desc()).paginate(page, per_page=8,
                                                                                                      error_out=False)
    comInfor = pagination.items
    return render_template('interncompany.html', form=form, Permission=Permission, pagination=pagination,
                           comInfor=comInfor)


# 实习日志列表
@main.route('/myjournalList', methods=['GET'])
@login_required
def myjournalList():
    comInfor = db.session.execute(
        'select DISTINCT start,end,i.comId comId,comName from InternshipInfor i,ComInfor c where i.comId=c.comId and i.stuId=%s'
        ' order BY i.internStatus  ' % current_user.stuId)
    return render_template('myJournalList.html', comInfor=comInfor, Permission=Permission)


# 填写实习日志
@main.route('/addjournal/<int:comId>', methods=['GET', 'POST'])
@login_required
def addjournal(comId):
    form = journalForm()
    if form.validate_on_submit():
        # workend = datetime.datetime.strptime(form.workStart.data, '%Y-%m-%d').date()
        workend = form.workStart.data
        journal = Journal(stuId=current_user.stuId, workStart=form.workStart.data, weekNo=form.weekNo.data,
                          workEnd=workend, comId=comId,
                          mon=form.mon.data, tue=form.tue.data, wed=form.wed.data, thu=form.thu.data,
                          fri=form.fri.data)
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


# 个人日志详情
@main.route('/myjournal/<int:comId>', methods=['GET'])
@login_required
def myjournal(comId):
    j = Journal.query.filter_by(stuId=current_user.stuId, comId=comId).count()
    if j > 0:
        student = Student.query.filter_by(stuId=current_user.stuId).first()
        com = ComInfor.query.filter_by(comId=comId).first()
        journal = db.session.execute('select * from Journal where stuId=%s and comId=%s' % (current_user.stuId, comId))
        return render_template('myjournal.html', Permission=Permission, journal=journal, student=student, com=com)
    else:

        flash('您还没有在此企业的实习日志，马上填写您的实习日志吧！')
        return redirect(url_for('.addjournal', comId=comId))


# 管理员\普通教师\审核教师
# 特定企业的实习学生列表
@main.route('/comInternList/<int:comId>', methods=['GET', 'POST'])
@login_required
def studentList(comId):
    form = searchform()
    page = request.args.get('page', 1, type=int)
    comName = ComInfor.query.filter(ComInfor.comId==comId).with_entities(ComInfor.comName).first()[0]
    # filter过滤当前特定企业ID
    pagination = Student.query.join(InternshipInfor).filter(InternshipInfor.comId==comId).order_by(Student.grade).paginate(page, per_page=8, error_out=False)
    student = pagination.items
    for stu in student:
        internStatus = InternshipInfor.query.filter_by(comId=comId, stuId=stu.stuId, internStatus=0).count()
        session[stu.stuId] = internStatus
    return render_template('studentList.html', form=form, pagination=pagination, student=student, Permission=Permission, comId=comId, comName=comName)



# 实习企业中学生的实习信息
@main.route('/studetail', methods=['GET'])
@login_required
def studetail():
    stuId = request.args.get('stuId')
    comId = request.args.get('comId')
    student = Student.query.filter_by(stuId=current_user.stuId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    internship = InternshipInfor.query.filter_by(stuId=stuId, comId=comId).first()
    dirctTea = DirctTea.query.filter_by(stuId=stuId, comId=comId).all()
    return render_template('stuInten.html', Permission=Permission, student=student, comInfor=comInfor,
                           internship=internship, stuId=stuId, comId=comId, dirctTea=dirctTea)


# 管理员\普通教师\审核教师
# 学生实习信息中学生列表
# 学生信息 -- 实习学生列表
@main.route('/stuList', methods=['GET', 'POST'])
@login_required
def stuList():
    # 与学生日志中的学生列表共用一个模板，journal作判断
    journal = False
    form = searchform()
    page = request.args.get('page', 1, type=int)
    pagination = Student.query.join(InternshipInfor).order_by(Student.grade).paginate(page, per_page=8,error_out=False)
    student = pagination.items
    # 记录学生实习信息条数
    for stu in student:
        n = InternshipInfor.query.filter_by(stuId=stu.stuId).count()
        session[stu.stuId] = n
    # 实习状态
    for stu in student:
        internStatus = InternshipInfor.query.filter_by(stuId=stu.stuId, internStatus=0).count()
        session[stu.stuId] = internStatus
    return render_template('stuList.html', form=form, pagination=pagination, student=student, Permission=Permission,journal=journal)


# 批量审核企业信息
@main.route('/allcomCheck', methods=['GET', 'POST'])
@login_required
def allcomCheck():
    form = searchform()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.filter_by(comCheck=0).order_by(ComInfor.comDate).paginate(page, per_page=8,
                                                                                          error_out=False)
    comInfor = pagination.items
    return render_template('allcomCheck.html', form=form, Permission=Permission, comInfor=comInfor,
                           pagination=pagination)


# 批量删除企业信息
@main.route('/allcomDelete', methods=['GET', 'POST'])
@login_required
def allcomDelete():
    form = searchform()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.order_by(ComInfor.comDate).paginate(page, per_page=8,
                                                                    error_out=False)
    comInfor = pagination.items
    return render_template('allcomDelete.html', form=form, Permission=Permission, comInfor=comInfor,
                           pagination=pagination)


# 学生的实习企业列表,id为stuId
@main.route('/stuInternList', methods=['GET', 'POST'])
@login_required
def stuInternList():
    id = request.args.get('id')
    # 与学生的企业日志列表共用一个模板，journal作判断
    journal = False
    stu = Student.query.filter_by(stuId=id).first()
    comInfor = db.session.execute(
        'select DISTINCT comName,comPhone,c.comId,start,end,internCheck from InternshipInfor i,ComInfor c where i.comId=c.comId'
        ' and i.stuId=%s order BY i.internCheck  ' % id)
    return render_template('stuInternList.html', stuName=stu.stuName, stuId=stu.stuId, Permission=Permission,comInfor=comInfor, journal=journal)


# 学生日志中学生信息列表
@main.route('/stuJourList', methods=['GET', 'POST'])
@login_required
def stuJourList():
    # 与学生实习信息中的学生列表共用一个模板，journal作判断
    journal = True
    form = searchform()
    page = request.args.get('page', 1, type=int)
    pagination = Student.query.join(Journal).order_by(Student.grade).paginate(page, per_page=8,error_out=False)
    student = pagination.items
    # 记录学生日志数
    for stu in student:
        n = Journal.query.filter_by(stuId=stu.stuId).count()
        session[stu.stuId] = n
    return render_template('stuList.html', form=form, pagination=pagination, student=student, Permission=Permission,
                           journal=journal)


# 学生的企业日志列表,id为stuId
@main.route('/comJourList', methods=['GET', 'POST'])
@login_required
def comJourList():
    id = request.args.get('id')
    # 与学生的实习企业列表共用一个模板，journal作判断
    journal = True
    print(id)
    stu = Student.query.filter_by(stuId=id).first()
    comInfor = db.session.execute(
        'select DISTINCT comName,comPhone,c.comId,start,end,internCheck from Journal j , InternshipInfor i,ComInfor c where c.comId=j.comId '
        'and i.stuId=j.stuId and i.comId=c.comId and j.stuId=%s' % id)
    return render_template('stuInternList.html', stuName=stu.stuName, stuId=stu.stuId, Permission=Permission,
                           comInfor=comInfor, journal=journal)


# 学生日志详情
@main.route('/stuJour', methods=['GET'])
@login_required
def stuJour():
    comId = request.args.get('comId')
    stuId = request.args.get('stuId')
    student = Student.query.filter_by(stuId=stuId).first()
    com = ComInfor.query.filter_by(comId=comId).first()
    journal = db.session.execute('select * from Journal where stuId=%s and comId=%s' % (stuId, comId))
    return render_template('myjournal.html', Permission=Permission, journal=journal, student=student, com=com)


# 学生用户列表
@main.route('/stuUserList', methods=['GET', 'POST'])
@login_required
def stuUserList():
    form = searchform()
    page = request.args.get('page', 1, type=int)
    pagination = Student.query.order_by(Student.grade.desc()).paginate(page, per_page=8, error_out=False)
    student = pagination.items
    for stu in student:
        session[stu.stuId] = stu.role.roleName
    return render_template('stuUserList.html', pagination=pagination, form=form, Permission=Permission,
                           student=student)


# 添加学生用户
@main.route('/addStudent', methods=['GET', 'POST'])
@login_required
def addStudent():
    stuform = stuForm()
    print(stuform.sex.data)
    if stuform.validate_on_submit():
        stu = Student(stuName=stuform.stuName.data, stuId=stuform.stuId.data, sex=stuform.sex.data,
                      institutes=stuform.institutes.data, major=stuform.major.data, classes=stuform.classes.data,
                      grade=stuform.grade.data)
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


# 教师用户列表
@main.route('/teaUserList', methods=['GET', 'POST'])
@login_required
def teaUserList():
    form = searchform()
    page = request.args.get('page', 1, type=int)
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


# 系统角色列表
@main.route('/roleList', methods=['GET', 'POST'])
@login_required
def roleList():
    role = Role.query.all()
    return render_template('roleList.html', Permission=Permission, role=role)


# 查询最大的企业Id
def getMaxComId():
    res = db.session.query(func.max(ComInfor.comId).label('max_comId')).one()
    return res.max_comId


# 添加角色,靠你们改善这个蠢方法了,\r\n不能换行，导致角色列表里的describe不能显全
@main.route('/addRole', methods=['GET', 'POST'])
@login_required
def addRole():
    form = permissionForm()
    p = []
    a = 0
    if form.validate_on_submit():
        if form.COM_INFOR_SEARCH.data:
            p.append('企业信息查看\r\n')
            a = eval(form.COM_INFOR_SEARCH.description) | a
        if form.COM_INFOR_EDIT.data:
            a = eval(form.COM_INFOR_EDIT.description) | a
            p.append('企业信息编辑\r\n')
        if form.COM_INFOR_CHECK.data:
            a = eval(form.COM_INFOR_CHECK.description) | a
            p.append('企业信息审核\r\n')
        if form.INTERNSHIP_LIST.data:
            a = eval(form.INTERNSHIP_LIST.description) | a
            p.append('实习企业信息列表\r\n')
        if form.STU_INFOR_LIST.data:
            a = eval(form.STU_INFOR_LIST.description) | a
            p.append('学生实习信息列表\r\n')
        if form.STU_INFOR_SEARCH.data:
            a = eval(form.STU_INFOR_SEARCH.description) | a
            p.append('学生实习信息查看\r\n')
        if form.STU_INFOR_EDIT.data:
            a = eval(form.STU_INFOR_EDIT.description) | a
            p.append('学生实习信息编辑\r\n')
        if form.STU_INFOR_CHECK.data:
            a = eval(form.STU_INFOR_CHECK.description) | a
            p.append('学生实习信息审核\r\n')
        if form.STU_INFOR_EXPORT.data:
            a = eval(form.STU_INFOR_EXPORT.description) | a
            p.append('学生实习信息导出\r\n')
        if form.STU_JOUR_SEARCH.data:
            a = eval(form.STU_JOUR_SEARCH.description) | a
            p.append('学生实习日志查看\r\n')
        if form.STU_JOUR_EDIT.data:
            a = eval(form.STU_JOUR_EDIT.description) | a
            p.append('学生实习日志编辑\r\n')
        if form.STU_JOUR_CHECK.data:
            a = eval(form.STU_JOUR_CHECK.description) | a
            p.append('学生实习日志审核\r\n')
        if form.STU_JOUR_EXPORT.data:
            a = eval(form.STU_JOUR_EXPORT.description) | a
            p.append('学生实习日志导出\r\n')
        if form.STU_SUM_SEARCH.data:
            a = eval(form.STU_SUM_SEARCH.description) | a
            p.append('学生实习总结查看\r\n')
        if form.STU_SUM_EDIT.data:
            a = eval(form.STU_SUM_EDIT.description) | a
            p.append('学生实习总结编辑\r\n')
        if form.STU_SUM_EXPORT.data:
            a = eval(form.STU_SUM_EXPORT.description) | a
            p.append('学生实习总结导出\r\n')
        if form.STU_SUM_CHECK.data:
            a = eval(form.STU_SUM_CHECK.description) | a
            p.append('学生实习总结审核\r\n')
        if form.STU_SCO_SEARCH.data:
            a = eval(form.STU_SCO_SEARCH.description) | a
            p.append('学生实习成果查看\r\n')
        if form.STU_SCO_EDIT.data:
            a = eval(form.STU_SCO_EDIT.description) | a
            p.append('学生实习成果编辑\r\n')
        if form.STU_SCO_EXPORT.data:
            a = eval(form.STU_SCO_EXPORT.description) | a
            p.append('学生实习成果导出\r\n')
        if form.ADMIN.data:
            a = eval(form.ADMIN.description) | a
            p.append('管理\r\n')
        if form.STU_INFOR_IMPORT.data:
            a = eval(form.STU_INFOR_IMPORT.description) | a
            p.append('学生信息导入\r\n')
        if form.TEA_INFOR_IMPORT.data:
            a = eval(form.TEA_INFOR_IMPORT.description) | a
            p.append('老师信息导入\r\n')
        if form.PERMIS_MANAGE.data:
            a = eval(form.PERMIS_MANAGE.description) | a
            p.append('权限管理\r\n')
        per = hex(a)
        print(per)
        describe = ''.join(p)
        print(describe)
        id = getMaxRoleId() + 1
        print(id)
        role = Role(roleName=form.roleName.data, roleDescribe=describe, permission=per, roleId=id)
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


# 查询最大的角色Id
def getMaxRoleId():
    res = db.session.query(func.max(Role.roleId).label('max_roleId')).one()
    return res.max_roleId
