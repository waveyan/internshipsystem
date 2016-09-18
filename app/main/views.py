# -*- coding: utf-8 -*-

from flask import render_template, url_for, flash, redirect, request, session, send_file
from .form import searchForm, comForm, internshipForm, journalForm, stuForm, teaForm, permissionForm, schdirteaForm, \
    comdirteaForm, xSumScoreForm
from . import main
from ..models import Permission, InternshipInfor, ComInfor, SchDirTea, ComDirTea, Student, Journal, Role, Teacher, \
    not_student_login, update_intern_internStatus, update_intern_jourCheck, Summary,Major,Grade,Classes,update_grade_major_classes,Visit,Visit_Intern
from flask.ext.login import current_user, login_required
from .. import db
from sqlalchemy import func, desc, and_, distinct
from datetime import datetime, timedelta, date
import xlwt, xlrd, os, random, subprocess, re,shutil
from collections import OrderedDict
from werkzeug.utils import secure_filename



# -----------------------------统计----------------------------------------
# 统计--地域统计图
@main.route('/statistics_area_visual', methods=['GET', 'POST'])
def statistics_area_visual():
    comlist = []
    index = 0
    cominfor = db.session.execute(
        'select comAddress, sum(students) from ComInfor group by comAddress order by sum(students) desc')
    for com in cominfor:
        if index < 6:
            # com[1] 为学生人数
            comlist.append({'comAddress': com.comAddress, 'students': com[1]})
            index = index + 1
            if index == 6:
                comlist.append({'comAddress': '其他', 'students': 0})
        else:
            comlist[6]['students'] = comlist[6]['students'] + com[1]
    return render_template('statistics_area_visual.html', Permission=Permission, comlist=comlist)


# 统计--企业统计图
@main.route('/statistics_com_visual', methods=['GET', 'POST'])
def statistics_com_visual():
    comlist = []
    index = 0
    cominfor = db.session.execute('select comId, comName, students from ComInfor order by students desc')
    for com in cominfor:
        if index < 6:
            comlist.append({'comId': com.comId, 'comName': com.comName, 'students': com.students})
            index = index + 1
            if index == 6:
                comlist.append({'comName': '其他', 'students': 0})
        else:
            comlist[6]['students'] = comlist[6]['students'] + com.students
    return render_template('statistics_com_visual.html', Permission=Permission, comlist=comlist)


# 统计--企业排行
@main.route('/statistics_com_rank', methods=['GET', 'POST'])
@login_required
def statistics_com_rank():
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.filter(ComInfor.students != 0).order_by(ComInfor.students.desc()).paginate(page,
                                                                                                           per_page=8,
                                                                                                           error_out=False)
    comInfor = pagination.items
    return render_template('statistics_com_rank.html', form=form, Permission=Permission, pagination=pagination,
                           comInfor=comInfor)


# 统计--地域排行
@main.route('/statistics_area_rank', methods=['GET', 'POST'])
@login_required
def statistics_area_rank():
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.filter(ComInfor.students != 0).order_by(ComInfor.students.desc()).paginate(page,
                                                                                                           per_page=8,
                                                                                                           error_out=False)
    comInfor = pagination.items
    return render_template('statistics_area_rank.html', form=form, Permission=Permission, pagination=pagination,
                           comInfor=comInfor)


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
    form = searchForm()
    grade = {}
    major = {}
    classes = {}
    page = request.args.get('page', 1, type=int)
    if current_user.roleId == 0:
        if session['message']['0'] == 1:
            try:
                db.session.execute('update Student set internCheck=0 where stuId=%s' % current_user.stuId)
                session['message']['0'] = 0
            except Exception as e:
                print('message:', e)
                flash('error!!!')
                return redirect('/')
        stuId = current_user.stuId
        student = Student.query.filter_by(stuId=stuId).first()
        internship = InternshipInfor.query.filter_by(stuId=stuId).all()
        # 让添加实习企业 addcominfor 下一步跳转到 addinternship
        if internship is None:
            flash('您还没完成实习信息的填写，请完善相关实习信息！')
            return redirect(url_for('.addcominfor', from_url='stuInternList'))
        else:
            pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
                .add_columns(ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start,
                             InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck) \
                .filter(InternshipInfor.stuId == stuId).order_by(
                func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
            internlist = pagination.items
            return render_template('stuInternList.html', internlist=internlist, Permission=Permission,
                                   student=student, pagination=pagination, form=form,
                                   grade=grade, major=major, classes=classes)
    elif current_user.can(Permission.STU_INTERN_LIST):
        # 函数返回的intern已经join了Student
        intern = create_intern_filter(grade, major, classes, 0)
        intern_org = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId).outerjoin(
            Teacher, Teacher.teaId == InternshipInfor.icheckTeaId) \
            .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, ComInfor.comId,
                         InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                         InternshipInfor.internCheck, InternshipInfor.address, InternshipInfor.task, Teacher.teaName,
                         InternshipInfor.opinion, InternshipInfor.icheckTime) \
            .order_by(func.field(InternshipInfor.internStatus, 1, 0, 2))
        pagination = intern_org.paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        # 批量导出实习excel表
        if request.method == "POST" and current_user.can(Permission.STU_INTERN_EDIT):
            isexport = request.form.get('isexport')
            if isexport:
                file_path = excel_export(excel_export_intern, intern_org)
                return export_download(file_path)
        return render_template('stuInternList.html', internlist=internlist, Permission=Permission,
                               pagination=pagination, form=form, grade=grade, classes=classes, major=major)
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
                                    comEmail=form.comEmail.data, comProvince=form.comProvince.data,comFax=form.comFax.data, comCheck=2)
            else:
                comInfor = ComInfor(comName=form.comName.data, comBrief=form.comBrief.data,
                                    comAddress=form.comAddress.data,
                                    comUrl=form.comUrl.data, comMon=form.comMon.data, comContact=form.comContact.data,
                                    comProject=form.comProject.data, comStaff=form.comStaff.data,
                                    comPhone=form.comPhone.data,
                                    comEmail=form.comEmail.data, comProvince=form.comProvince.data,comFax=form.comFax.data)
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
            if start < now:
                if end <= now:
                    internStatus = 2  # 实习结束
                    print('this is 1')
                if end > now:
                    internStatus = 1  # 实习中
                    print('this is 2')
            elif start > now:
                internStatus = 0  # 待实习
                print('this is 3')
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
                j = j + 1
                cteaValue = request.form.get('cteaName%s' % j)
                if cteaValue:
                    comdirtea = ComDirTea(
                        stuId=stuId,
                        cteaName=cteaValue,
                        comId=comId,
                        cteaDuty=request.form.get('cteaDuty%s' % j),
                        cteaEmail=request.form.get('cteaEmail%s' % j),
                        cteaPhone=request.form.get('cteaPhone%s' % j)
                    )
                    db.session.add(comdirtea)
                else:
                    break
            # 先commit internship,更新等等需用到的internId
            try:
                db.session.add(internship)
                db.session.commit()
            except Exception as e:
                print('添加校外指导老师：', e)
                db.session.rollback()
                flash('添加实习信息失败，请重试！')
                return redirect('/')
            # 若所选企业未被审核通过,且用户有审核权限,自动审核通过企业
            if current_user.can(Permission.COM_INFOR_CHECK):
                try:
                    db.session.execute('update ComInfor set comCheck=2 where comId=%s' % comId)
                except Exception as e:
                    db.session.rollback()
                    print(datetime.now(), '/addinternship 审核企业失败:', e)
                    flash('所选企业审核失败,请重试')
                    return redirect('/')




            # 初始化日志和总结成果
            db.session.commit()
            internId = int(InternshipInfor.query.order_by(desc(InternshipInfor.Id)).first().Id)
            journal_init(internId)
            summary_init(internId)
            # 更新累计实习人数
            cominfor = ComInfor.query.filter_by(comId=comId).first()
            if cominfor.students:
                db.session.execute('update ComInfor set students=students+1')
            else:
                db.session.execute('update ComInfor set students=1')

            #上传协议书
            if request.files.getlist('image'):
                for i in request.files.getlist('image'):
                    i.save('%s/%s/agreement/%s' % (STORAGE_FOLDER, internId,i.filename))

            db.session.commit()
            flash('提交实习信息成功！')
            return redirect(url_for('.update_intern_filter',flag=5))
    except Exception as e:
        print("实习信息：", e)
        db.session.rollback
        flash('提交实习信息失败，请重试！')
        return redirect(url_for('.addcominfor'))
    return render_template('addinternship.html', iform=iform, schdirteaform=schdirteaform, comdirteaform=comdirteaform,
                           Permission=Permission)


# 普通老师对于自己的指导学生, 带有'审核老师'的权限
def is_schdirtea(stuId):
    if hasattr(current_user, 'teaId'):
        teaId = current_user.teaId
        flag = hasattr(SchDirTea.query.filter_by(stuId=stuId, teaId=teaId).first(), 'Id')
        return flag


# 学生个人实习信息
@main.route('/xIntern', methods=['GET', 'POST'])
@login_required
def xIntern():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    internId = request.args.get('internId')
    comId = InternshipInfor.query.filter_by(Id=internId).first().comId
    student = Student.query.filter_by(stuId=stuId).first()
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    schdirtea = SchDirTea.query.filter_by(stuId=stuId).all()
    comdirtea = ComDirTea.query.filter_by(stuId=stuId, comId=comId).all()
    #实习协议图片路径
    path=[]
    p=os.path.join(os.path.abspath('.'),"app/static/storage/%s/agreement"%internId)
    if os.path.exists(p):
        for x in os.listdir(p):
            path.append(os.path.join(p[p.find('/static'):],x))
    print('33333333333333333',x)
    # 导出实习excel表
    intern_excel = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(ComInfor,
                                                                                                    InternshipInfor.comId == ComInfor.comId).outerjoin(
        Teacher, Teacher.teaId == InternshipInfor.icheckTeaId) \
        .filter(InternshipInfor.Id == internId) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, ComInfor.comId,
                     InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck, InternshipInfor.address, InternshipInfor.task, Teacher.teaName,
                     InternshipInfor.opinion, InternshipInfor.icheckTime)
    # 若普通老师为学生的指导老师, 赋予其权限
    schdirtea_can = is_schdirtea(stuId)
    if request.method == "POST":
        if current_user.roleId == 0 or current_user.can(Permission.STU_INTERN_SEARCH) or schdirtea_can:
            isexport = request.form.get('isexport')
            if isexport:
                file_path = excel_export(excel_export_intern, intern_excel)
                return export_download(file_path)
    return render_template('xIntern.html', Permission=Permission, comInfor=comInfor,
                           schdirtea=schdirtea, comdirtea=comdirtea, internship=internship, student=student, schdirtea_can=schdirtea_can, path=path)


# 审核通过实习信息
@main.route('/xIntern_comfirm', methods=["POST", "GET"])
@not_student_login
def xIntern_comfirm():
    stuId = request.form.get('stuId')
    schdirtea_can = is_schdirtea(stuId)
    if current_user.can(Permission.STU_INTERN_CHECK) or schdirtea_can:
        internId = request.form.get('internId')
        internCheck = request.form.get('internCheck')
        # stuId = request.form.get('stuId')
        opinion = request.form.get('opinion')
        comId = InternshipInfor.query.filter_by(Id=internId).first().comId
        com = ComInfor.query.filter_by(comId=comId).first()
        checkTime = datetime.now()
        checkTeaId = current_user.get_id()
        try:
            if opinion:
                db.session.execute(
                    'update InternshipInfor set internCheck=%s, icheckTime="%s", icheckTeaId="%s", opinion="%s" where Id=%s' % (
                        internCheck, checkTime, checkTeaId, opinion, internId))
            else:
                db.session.execute(
                    'update InternshipInfor set internCheck=%s, icheckTime="%s", icheckTeaId="%s" where Id=%s' % (
                        internCheck, checkTime, checkTeaId, internId))
            # 若所选企业未被审核通过,且用户有审核权限,自动审核通过企业
            if com.comCheck != 2 and current_user.can(Permission.COM_INFOR_CHECK):
                db.session.execute('update ComInfor set comCheck=2 where comId=%s' % comId)
            # 作消息提示
            db.session.execute('update Student set internCheck=1 where stuId=%s' % stuId)
        except Exception as e:
            db.session.rollback()
            print(datetime.now(), ":", current_user.get_id(), "审核实习申请失败", e)
            flash("实习申请审核失败")
            return redirect("/")
        flash("实习申请审核成功")
    return redirect(url_for('.stuInternList', stuId=stuId))


# 修改实习信息
@main.route('/xInternEdit', methods=['GET', 'POST'])
@login_required
def xInternEdit():
    if request.form.get('stuId'):
        stuId = request.form.get('stuId')
        internId = request.form.get('internId')
    else:
        stuId = request.args.get('stuId')
        internId = request.args.get('internId')
    if current_user.roleId == 0:
        stuId = current_user.stuId
    elif not current_user.can(Permission.STU_INTERN_EDIT):
        if is_schdirtea(stuId) is not True:
            flash('非法操作')
            return redirect('/')
    comId = InternshipInfor.query.filter_by(Id=internId).first().comId
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
    #图片路径
    filePath=[]
    imageName=[]
    p=os.path.join(os.path.abspath('.'),"app/static/storage/%s/agreement"%internId)
    if os.path.exists(p):
        for x in os.listdir(p):
            imageName.append(x)
            filePath.append(os.path.join(p,x))
    filename=request.args.get('filename')
    #协议书删除
    if filename:
        for file in filePath:
            if file.find(filename)!=-1:
                os.remove(file)
                flash('删除成功！')
                return redirect(url_for('.xInternEdit',stuId=stuId,internId=internId))
    if request.method=='POST':
        #上传协议书
        if request.files.getlist('image'):
            for i in request.files.getlist('image'):
                i.save('%s/%s/agreement/%s' % (STORAGE_FOLDER, internId,i.filename))
        flash('上传成功！')
        return redirect(url_for('.xInternEdit',stuId=stuId,internId=internId))
    return render_template('xInternEdit.html', Permission=Permission, comInfor=comInfor, schdirtea=schdirtea, \
                           comdirtea=comdirtea, internship=internship, student=student, stuform=stuform, \
                           comform=comform, \
                           internform=internform, schdirteaform=schdirteaform, comdirteaform=comdirteaform,imageName=imageName)


# 修改实习信息 个人实习信息--实习岗位信息
@main.route('/xInternEdit_intern', methods=["POST", "GET"])
@login_required
def xInternEdit_intern():
    if current_user.roleId == 0:
        stuId = current_user.stuId
        internCheck = 0
        permission = True
    else:
        stuId = request.form.get('stuId')
        if current_user.can(Permission.STU_INTERN_CHECK) or is_schdirtea(stuId):
            internCheck = 2
            permission = True
    # elif current_user.can(Permission.STU_INTERN_CHECK):
    #     stuId = request.form.get('stuId')
    #     internCheck = 2
    if permission:
        task = request.form.get('task')
        address = request.form.get('address')
        start = request.form.get('start')
        end = request.form.get('end')
        time = datetime.now().date()
        comId = request.form.get("comId")
        internId = request.form.get("internId")
        # if task is None or address is None or start is None or end is None or time is None or comId is None or stuId is None or internId is None:
        if not (task and address and start and end and time and comId and stuId and internId):
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
        # 若审核通过, 则添加审核时间和教师工号
        if internCheck == 2:
            icheckTime = datetime.now().date()
            icheckTeaId = current_user.get_id()
            db.session.execute('update InternshipInfor set icheckTime=%s, icheckTeaId=%s where Id=%s' % (icheckTime, icheckTeaId, internId))
        # 实习信息修改,日志跟随变动
        journal_migrate(internId)
        return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))


# 修改实习信息 个人实习信息--企业指导老师
@main.route('/xInternEdit_comdirtea', methods=["POST"])
@login_required
def xInternEdit_comdirtea():
    if current_user.roleId == 0:
        stuId = current_user.stuId
        permission = True
    else:
        stuId = request.form.get('stuId')
        if is_schdirtea(stuId):
            permission = True
    if permission:
        Id = request.form.get("Id")
        comId = request.form.get('comId')
        start = request.form.get('start')
        teaName = request.form.get('cteaName')
        teaDuty = request.form.get('cteaDuty')
        teaPhone = request.form.get('cteaPhone')
        teaEmail = request.form.get('cteaEmail')
        internId = request.form.get("internId")
        # if teaName is None or comId is None or internId is None or stuId is None:
        if not (teaName and comId and internId and stuId):
            flash("修改实习信息失败,请重试")
            return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))
        db.session.execute(' \
            update ComDirTea set \
            cteaName = "%s", \
            cteaDuty = "%s", \
            cteaPhone ="%s", \
            cteaEmail = "%s" \
            where Id=%s'
                           % (teaName, teaDuty, teaPhone, teaEmail, Id)
                           )
        flash("实习信息修改成功")
        return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))


# 实习,日志,总结成果的单个删除
@main.route('/intern_delete', methods=['POST'])
@login_required
def comfirmDeletreJournal_Intern():
    internId = request.form.get('internId')
    from_url = request.form.get('from_url')
    if current_user.roleId == 0:
        stuId = current_user.stuId
        permission = True
    else:
        stuId = request.form.get('stuId')
        if from_url == 'xSum':
            permission = current_user.can(Permission.STU_INTERN_CHECK) and current_user.can(
                Permission.STU_JOUR_CHECK) and current_user.can(Permission.STU_SUM_SCO_CHECK)
        elif is_schdirtea(stuId):
            permission = True
        else:
            permission = current_user.can(Permission.STU_INTERN_CHECK) and current_user.can(Permission.STU_JOUR_CHECK)
    # if not permission:
    #     flash('非法操作')
    #     return redirect('/')
    # else:
    if permission:
        try:
            if from_url == 'xSum':
                db.session.execute('delete from Summary where internId=%s' % internId)
            # 企业指导老师,日志,实习一同删除
            comId = InternshipInfor.query.filter_by(Id=internId).first().comId
            db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s' % (stuId, comId))
            db.session.execute('delete from Journal where internId=%s and stuId=%s' % (internId, stuId))
            db.session.execute('delete from InternshipInfor where Id=%s and stuId=%s' % (internId, stuId))
            # 企业累计实习人数减一
            db.session.execute('update ComInfor set students = students -1 where comId=%s' % comId)
            # 删除总结成果--文件目录
            subprocess.call('rm %s/%s -r' % (STORAGE_FOLDER, internId), shell=True)
            flash('删除相关实习信息成功')
            if from_url == "xIntern":
                return redirect(url_for('.stuInternList'))
            elif from_url == "xJournal":
                return redirect(url_for('.stuJournalList'))
            elif from_url == 'xSum':
                return redirect(url_for('.stuSumList'))
        except Exception as e:
            print('删除日志和实习信息失败:', e)
            db.session.rollback()
            flash('提交实习信息失败，请重试！')
            if from_url == "/xIntern":
                return redirect(url_for('.stuInternList'))
            elif from_url == "/xJournal":
                return redirect(url_for('.stuJournalList'))
            elif from_url == 'xSum':
                return redirect(url_for('.stuSumList'))


# 企业详细信息,方法POST不可删除，在修改返回时有用
@main.route('/cominfor', methods=['GET', 'POST'])
@login_required
def cominfor():
    id = request.args.get('id')
    com = ComInfor.query.filter_by(comId=id).first()
    # 批量导出实习excel表
    if request.method == "POST" and current_user.can(Permission.COM_INFOR_SEARCH):
        isexport = request.form.get('isexport')
        if isexport:
            return excel_export(excel_export_com, ComInfor.query.filter_by(comId=id).all())
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
    if request.method == "POST":
        isexport = request.form.get('isexport')
        if isexport:
            file_path = excel_export(excel_export_com, com.all())
            return export_download(file_path)
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


# interncompany搜索,只对企业名称存在的关键字作搜索
@main.route('/com_search', methods=['GET', 'POST'])
@login_required
def com_search():
    form = searchForm()
    comInfor = []
    selectCom = request.args.get('selectCom')
    if request.method == 'POST':
        key = form.key.data
        cominfor = ComInfor.query.all()
        for c in cominfor:
            if c.comName.find(key) != -1:
                comInfor.append(c)
    return render_template('comSearchResult.html', num=len(comInfor), form=form, Permission=Permission,
                           comInfor=comInfor,
                           key=key, selectCom=selectCom)


# internshipInfor搜索,支持学生姓名，学生编号，企业名称搜索
@main.route('/intern_search', methods=['GET', 'POST'])
@login_required
def intern_search():
    form = searchForm()
    internList = []
    journal = None
    sum = None
    if request.method == 'POST':
        internship = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId) \
            .join(ComInfor, ComInfor.comId == InternshipInfor.comId).add_columns(Student.stuId, Student.stuName,
                                                                                 ComInfor.comName \
                                                                                 , InternshipInfor.start,
                                                                                 InternshipInfor.end,
                                                                                 InternshipInfor.internCheck \
                                                                                 , InternshipInfor.internStatus,
                                                                                 InternshipInfor.Id).all()
        for intern in internship:
            if intern.stuName == form.key.data:
                internList.append(intern)
            if intern.stuId == form.key.data:
                internList.append(intern)
            if intern.comName.find(form.key.data) != -1:
                internList.append(intern)
    return render_template('internSearchResult.html', Permission=Permission, form=form, key=form.key.data,
                           num=len(internList), \
                           internList=internList, journal=journal, sum=sum)


# journal搜索,支持学生姓名，学生编号，企业名称搜索
@main.route('/journal_search', methods=['GET', 'POST'])
@login_required
def journal_search():
    form = searchForm()
    journal = request.args.get('journal')
    sum = None
    internList = []
    if request.method == 'POST':
        internship = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId) \
            .join(ComInfor, ComInfor.comId == InternshipInfor.comId).add_columns(Student.stuId, Student.stuName,
                                                                                 ComInfor.comName \
                                                                                 , InternshipInfor.start,
                                                                                 InternshipInfor.end,
                                                                                 InternshipInfor.internCheck \
                                                                                 , InternshipInfor.internStatus,
                                                                                 InternshipInfor.Id).all()
        for intern in internship:
            if intern.stuName == form.key.data:
                internList.append(intern)
            if intern.stuId == form.key.data:
                internList.append(intern)
            if intern.comName.find(form.key.data) != -1:
                internList.append(intern)
    return render_template('internSearchResult.html', Permission=Permission, form=form, key=form.key.data,
                           num=len(internList), \
                           internList=internList, journal=journal, sum=sum)


# summary搜索,支持学生姓名，学生编号，企业名称搜索
@main.route('/sum_search', methods=['GET', 'POST'])
@login_required
def sum_search():
    form = searchForm()
    sum = request.args.get('sum')
    journal = None
    internList = []
    if request.method == 'POST':
        internship = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(ComInfor,
                                                                                                      ComInfor.comId == InternshipInfor.comId).join(
            Summary, Summary.internId == InternshipInfor.Id).add_columns(Student.stuId, Student.stuName,
                                                                         ComInfor.comName,
                                                                         InternshipInfor.start, InternshipInfor.end,
                                                                         Summary.sumCheck, Summary.sumScore,
                                                                         InternshipInfor.Id).all()
        for intern in internship:
            if intern.stuId == form.key.data:
                internList.append(intern)
            if intern.stuName == form.key.data:
                internList.append(intern)
            if intern.comName.find(form.key.data) != -1:
                internList.append(intern)
    return render_template("internSearchResult.html", form=form, Permission=Permission, journal=journal, sum=sum,
                           internList=internList, key=form.key.data, num=len(internList))


# user搜索,支持姓名，编号搜索
@main.route('/user_search', methods=['GET', 'POST'])
@login_required
def user_search():
    form = searchForm()
    tea = request.args.get('tea')
    teacher = []
    student = []
    if request.method == 'POST':
        if tea:
            tea = Teacher.query.all()
            for t in tea:
                if t.teaName == form.key.data:
                    teacher.append(t)
                if t.teaId == form.key.data:
                    teacher.append(t)
        else:
            stu = Student.query.all()
            for s in stu:
                if s.stuId == form.key.data:
                    student.append(s)
                if s.stuName == form.key.data:
                    student.append(s)
    return render_template("userSearchResult.html", Permission=Permission, student=student, tea=tea, teacher=teacher,
                           form=form, key=form.key.data, snum=len(student), tnum=len(teacher))


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
        try:
            for x in comId:
                db.session.execute("delete from ComInfor where comId = %s" % x)
        except Exception as e:
            db.session.rollback()
            print('批量删除企业信息：', e)
            flash('删除失败，请重试！')
        flash('删除成功！')
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
        com.comProvince=comform.comProvince.data
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
            print('修改企业信息', e)
            db.session.rollback()
            flash('修改失败，请重试！')
            return redirect(url_for('.editcominfor', comId=id))
    return render_template('editComInfor.html', Permission=Permission, com=com, comform=comform, cominfor=cominfor)


# 批量审核实习信息
@main.route('/stuIntern_allCheck', methods=['GET', 'POST'])
@not_student_login
def stuIntern_allCheck():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    form = searchForm()
    grade = {}
    classes = {}
    major = {}
    intern = create_intern_filter(grade, major, classes, 0)
    pagination_part = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, InternshipInfor.comId,
                     InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck) \
        .filter(InternshipInfor.internCheck != 2).order_by(InternshipInfor.internStatus)
    if current_user.can(Permission.COM_INFOR_CHECK):
        pagination = pagination_part.paginate(page, per_page=8, error_out=False)
    else:
        pagination = pagination_part.filter(ComInfor.comCheck == 2).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定实习审核通过
    if request.method == "POST":
        try:
            internId = request.form.getlist('approve[]')
            checkTime = datetime.now()
            checkTeaId = current_user.get_id()
            for x in internId:
                db.session.execute(
                    'update InternshipInfor set internCheck=2, icheckTime="%s", icheckTeaId="%s" where Id = %s' % (
                        checkTime, checkTeaId, x))
                # 作消息提示
                stuId = InternshipInfor.query.filter_by(Id=x).first().stuId
                db.session.execute('update Student set internCheck=1 where stuId=%s' % stuId)
                # 若所选企业未被审核通过,且用户有审核权限,自动审核通过企业
                comId = InternshipInfor.query.filter_by(Id=x).first().comId
                com = ComInfor.query.filter_by(comId=comId).first()
                if com.comCheck != 2:
                    db.session.execute('update ComInfor set comCheck=2 where comId=%s' % comId)
        except Exception as e:
            db.session.rollback()
            print(datetime.now(), ":", current_user.get_id(), "审核实习申请失败", e)
            flash("实习申请审核失败")
            return redirect("/")
        flash('实习信息审核成功')
        return redirect(url_for('.stuIntern_allCheck', page=pagination.page))
    return render_template('stuIntern_allCheck.html', Permission=Permission, internlist=internlist,
                           pagination=pagination, major=major, classes=classes, grade=grade, form=form)


# 批量删除实习信息
@main.route('/stuIntern_allDelete', methods=['GET', 'POST'])
@not_student_login
def stuIntern_allDelete():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    form = searchForm()
    grade = {}
    classes = {}
    major = {}
    intern = create_intern_filter(grade, major, classes, 0)
    pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
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
            # 删除总结成果--文件目录
            subprocess.call('rm %s/%s -r' % (STORAGE_FOLDER, x), shell=True)
        flash('实习信息删除成功')
        return redirect(url_for('.stuIntern_allDelete', page=pagination.page))
    return render_template('stuIntern_allDelete.html', Permission=Permission, internlist=internlist,
                           pagination=pagination, grade=grade, classes=classes, major=major, form=form)


# 批量审核日志
@main.route('/stuJournal_allCheck', methods=['GET', 'POST'])
@not_student_login
def stuJournal_allCheck():
    if not current_user.can(Permission.STU_JOUR_CHECK):
        flash("非法操作")
        return redirect('/')
    form = searchForm()
    grade = {}
    classes = {}
    major = {}
    intern = create_intern_filter(grade, major, classes, 1)
    now = datetime.now().date()
    page = request.args.get('page', 1, type=int)
    pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
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
        checkTime = datetime.now()
        checkTeaId = current_user.get_id()
        for x in internId:
            db.session.execute('update InternshipInfor set jourCheck=1 where Id=%s' % x)
            db.session.execute(
                'update Journal set jourCheck=1, jcheckTime="%s", jcheckTeaId=%s where internId=%s and workEnd<"%s"' % (
                    checkTime, checkTeaId, x, now))
            # 作消息提示
            stuId = InternshipInfor.query.filter_by(Id=x).first().stuId
            db.session.execute('update Student set jourCheck=1 where stuId=%s' % stuId)
        flash('日志审核成功')
        return redirect(url_for('.stuJournal_allCheck', page=pagination.page))
    return render_template('stuJournal_allCheck.html', Permission=Permission, pagination=pagination,
                           internlist=internlist, form=form, classes=classes, grade=grade, major=major)


# 批量删除日志
@main.route('/stuJournal_allDelete', methods=['GET', 'POST'])
@not_student_login
def stuJournal_allDelete():
    if not current_user.can(Permission.STU_JOUR_CHECK):
        flash("非法操作")
        return redirect('/')
    form = searchForm()
    grade = {}
    classes = {}
    major = {}
    intern = create_intern_filter(grade, major, classes, 1)
    now = datetime.now().date()
    page = request.args.get('page', 1, type=int)
    pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
        .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id,
                     InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck, InternshipInfor.jourCheck) \
        .filter(InternshipInfor.internCheck == 2).group_by(InternshipInfor.Id).order_by(
        func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
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
            # 删除总结成果--文件目录
            subprocess.call('rm %s/%s -r' % (STORAGE_FOLDER, x), shell=True)
        flash('日志删除成功')
        return redirect(url_for('.stuJournal_allDelete', page=pagination.page))
    return render_template('stuJournal_allDelete.html', Permission=Permission, pagination=pagination,
                           internlist=internlist, form=form, major=major, classes=classes, grade=grade)


# 学生日志
@main.route('/stuJournalList', methods=['GET', 'POST'])
@login_required
def stuJournalList():
    form = searchForm()
    grade = {}
    major = {}
    classes = {}
    page = request.args.get('page', 1, type=int)
    if current_user.roleId == 0:
        stuId = current_user.stuId
        if session['message']['1'] == 1:
            try:
                db.session.execute('update Student set jourCheck=0 where stuId=%s' % stuId)
                session['message']['1'] = 0
            except Exception as e:
                print('message:', e)
                flash('error!!!')
                return redirect('/')
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
            return render_template('stuJournalList.html', form=form, internlist=internlist, Permission=Permission,
                                   pagination=pagination, grade=grade, major=major, classes=classes)
    elif current_user.can(Permission.STU_JOUR_SEARCH):
        intern = create_intern_filter(grade, major, classes, flag=1)
        for x in intern:
            print (x.Id,'--------------')
        pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
            .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id,
                         InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                         InternshipInfor.internCheck, InternshipInfor.jourCheck) \
            .filter(InternshipInfor.internCheck == 2, InternshipInfor.internStatus != 0).group_by(InternshipInfor.Id).order_by(
            func.field(InternshipInfor.internStatus, 1, 2)).paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        for x in internlist:
            print(x.Id)
        # 批量导出实习excel表
        if request.method == "POST" and current_user.can(Permission.STU_JOUR_EDIT):
            isexport = request.form.get('isexport')
            print ('1111', isexport)
            if isexport:
                internIdList = []
                for x in internlist:
                    internIdList.append(x.Id)
                file_path = journal_export(internIdList)
                return export_download(file_path)
        return render_template('stuJournalList.html', form=form, internlist=internlist, Permission=Permission,
                               pagination=pagination, grade=grade, major=major, classes=classes)


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
    # 导出日志
    if request.method == "POST":
        if current_user.roleId == 0 or current_user.can(Permission.STU_JOUR_SEARCH):
            isexport = request.form.get('isexport')
            if isexport:
                file_path = journal_export([internId])
                return export_download(file_path)
    if current_user.roleId == 0:
        return render_template('xJournal.html', Permission=Permission, internship=internship, journal=journal,
                               student=student, comInfor=comInfor, pagination=pagination, page=page, now=now)
    else:
        if internship.internCheck == 2:
            return render_template('xJournal.html', Permission=Permission, internship=internship, journal=journal,
                                   student=student, comInfor=comInfor, pagination=pagination, page=page, now=now)
        else:
            flash("实习申请需审核后,才能查看日志")
            return redirect(url_for('.xIntern', stuId=stuId, internId=internId))


@main.route('/journal_comfirm', methods=['POST', 'GET'])
@not_student_login
def journal_comfirm():
    # 参数都是为了跳转 xJournal 做准备
    stuId = request.args.get('stuId')
    jourId = request.args.get('jourId')
    internId = request.args.get('internId')
    checkTime = datetime.now()
    checkTeaId = current_user.get_id()
    if current_user.can(Permission.STU_JOUR_CHECK):
        db.session.execute('update Journal set jourCheck=1, jcheckTime="%s", jcheckTeaId=%s where Id=%s' % (
            checkTime, checkTeaId, jourId))
        # 作消息提示
        db.session.execute('update Student set jourCheck=1 where stuId=%s' % stuId)
        # 检查是否需要更新 InternshipInfor.jourCheck
        jourCheck = Journal.query.filter(Journal.internId == internId, Journal.jourCheck == 0,
                                         Journal.workEnd < datetime.now().date()).count()
        if jourCheck == 0:
            db.session.execute('update InternshipInfor set jourCheck=1 where Id=%s' % internId)
            # 作消息提示
            db.session.execute('update Student set jourCheck=1 where stuId=%s' % stuId)
        flash("日志审核通过")
        return redirect(url_for('.stuJournalList'))
    else:
        # 非法操作,返回主页3
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
    if jour.jourCheck == 1 and current_user.roleId != 3:
        flash('日志已通过审核,无法修改')
        return redirect('/')
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


# 学生信息的筛选项(副导航栏)操作,对所选筛选项进行删除,0实习信息批量审核，
# 1实习信息批量删除，2日志列表，3日志批量审核，4,日志批量删除，5实习信息列表
# 6成果与总结列表,7成果与总结批量审核，8成果与总结批量删除
@main.route('/update_intern_filter', methods=['GET', 'POST'])
@login_required
def update_intern_filter():
    grade = request.args.get('grade')
    major = request.args.get('major')
    classes = request.args.get('classes')
    internStatus = request.args.get('internStatus')
    flag = request.args.get('flag')
    if grade is not None:
        session['major'] = None
        session['classes'] = None
        session['internStatus'] = None
        session['checkStatus'] = None

    elif major is not None:
        session['classes'] = None
        session['internStatus'] = None
        session['checkStatus'] = None
    elif classes is not None:
        session['internStatus'] = None
        session['checkStatus'] = None
    elif internStatus:
        session['checkStatus'] = None
    else:
        session['major'] = None
        session['classes'] = None
        session['grade'] = None
        session['internStatus'] = None
        session['checkStatus'] = None
    if flag == '0':
        return redirect(url_for('.stuIntern_allCheck'))
    elif flag == '1':
        return redirect(url_for('.stuIntern_allDelete'))
    elif flag == '2':
        return redirect(url_for('.stuJournalList'))
    elif flag == '3':
        return redirect(url_for('.stuJournal_allCheck'))
    elif flag == '4':
        return redirect(url_for('.stuJournal_allDelete'))
    elif flag == '5':
        return redirect(url_for('.stuInternList'))
    elif flag == '6':
        return redirect(url_for('.stuSumList'))
    elif flag == '7':
        return redirect(url_for('.stuSum_allCheck'))
    else:
        return redirect(url_for('.stuSum_allDelete'))



# -------------管理-----------------------------------------------------------------------------------
# 学生用户列表
@main.route('/stuUserList', methods=['GET', 'POST'])
@login_required
def stuUserList():
    # 非管理员,不能进入
    if not current_user.can(Permission.STU_INTERN_MANAGE):
        return redirect('/')
    form = searchForm()
    grade = {}
    classes = {}
    major = {}
    stu = create_stu_filter(grade, major, classes)
    page = request.args.get('page', 1, type=int)
    pagination = stu.paginate(page, per_page=8, error_out=False)
    student = pagination.items
    # 权限带修改
    if request.method == "POST" and current_user.can(Permission.STU_INTERN_MANAGE):
        isexport = request.form.get('isexport')
        if isexport:
            file_path = excel_export(excel_export_stuUser, student)
            return export_download(file_path)
    return render_template('stuUserList.html', pagination=pagination, form=form, Permission=Permission, student=student,
                           grade=grade, major=major, classes=classes)


# 学生用户信息的筛选项操作,对所选筛选项进行删除,flag=1批量设置
#flag=0批量删除，flag=2学生基本信息，else列表探访记录选择学生
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
        session['internStatus'] = None
    elif major is not None:
        session['sex'] = None
        session['classes'] = None
        session['internStatus'] = None
    elif classes is not None:
        session['sex'] = None
        session['internStatus'] = None
    else:
        session['major'] = None
        session['classes'] = None
        session['sex'] = None
        session['grade'] = None
        session['internStatus'] = None
    if flag == '1':
        return redirect(url_for('.allStuSet'))
    elif flag == '0':
        return redirect(url_for('.allStuDelete'))
    elif flag=='2':
        return redirect(url_for('.stuUserList'))
    else:
        return redirect(url_for('.selectStudent'))


# 添加学生用户
@main.route('/addStudent', methods=['GET', 'POST'])
@login_required
def addStudent():
    # 非管理员,不能进入
    if not current_user.can(Permission.STU_INTERN_MANAGE):
        return redirect('/')
    # user=Teacher.query.filter_by(teaId=current_user.teaId).first()
    stuform = stuForm()
    print('stuform',stuform.institutes)
    schdirteaform = schdirteaForm()
    if request.method == 'POST':
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
        i = 0
        while True:
            i = i + 1
            teaValue = request.form.get('teaId%s' % i)
            if teaValue:
                schdirtea = SchDirTea(
                    teaId=teaValue,
                    stuId=stuform.stuId.data,
                    steaName=request.form.get('teaName%s' % i),
                    steaDuty=request.form.get('teaDuty%s' % i),
                    steaPhone=request.form.get('teaPhone%s' % i),
                    steaEmail=request.form.get('teaEmail%s' % i)
                )
                db.session.add(schdirtea)
            else:
                break
        try:
            db.session.commit()
            flash('添加学生信息成功！')
            return redirect(url_for('.stuUserList'))
        except Exception as e:
            db.session.rollback()
            flash('添加学生信息失败请重试！')
            print('添加学生信息：', e)
            return redirect(url_for('.addStudent'))
    return render_template('addStudent.html', stuform=stuform, Permission=Permission, schdirteaform=schdirteaform)


# 修改学生用户信息
@main.route('/editStudent', methods=['GET', 'POST'])
@login_required
def editStudent():
    form = stuForm()
    schdirteaform = schdirteaForm()
    stuId = request.args.get('stuId')
    stu = Student.query.filter_by(stuId=stuId).first()
    schdirtea = SchDirTea.query.filter_by(stuId=stuId).all()
    if request.method == 'POST':
        try:
            for tea in schdirtea:
                db.session.delete(tea)
            stu.stuId = form.stuId.data
            stu.stuName = form.stuName.data
            stu.sex = request.form.get('sex')
            i = 0
            for name in request.form:
                print(name)
                if name.find('nteaId')!=-1:
                    i=i+1
            i=i+1
            stu.major = form.major.data
            stu.grade = form.grade.data
            stu.classes = form.classes.data
            db.session.add(stu)
            x=0
            while True:
                x=x+1
                teaId = request.form.get('nteaId%s' % x)
                if teaId:
                    nschdirtea = SchDirTea(
                        teaId=teaId,
                        stuId=form.stuId.data,
                        steaName=request.form.get('nteaName%s' % x),
                        steaDuty=request.form.get('nteaDuty%s' % x),
                        steaPhone=request.form.get('nteaPhone%s' % x),
                        steaEmail=request.form.get('nteaEmail%s' % x)
                    )
                    db.session.add(nschdirtea)
                elif x==i:
                    break
                    # 添加新老师
            j = 0
            while True:
                j = j + 1
                teaId = request.form.get('teaId%s' % j)
                if teaId:
                    schdirtea = SchDirTea(
                        teaId=teaId,
                        stuId=form.stuId.data,
                        steaName=request.form.get('teaName%s' % j),
                        steaDuty=request.form.get('teaDuty%s' % j),
                        steaPhone=request.form.get('teaPhone%s' % j),
                        steaEmail=request.form.get('teaEmail%s' % j)
                    )
                    db.session.add(schdirtea)
                else:
                    break
            db.session.commit()
            flash('修改成功！')
            return redirect(url_for('.stuUserList'))
        except Exception as e:
            print('修改学生用户信息：', e)
            db.session.rollback()
            flash('修改失败，请重试！')
            return redirect(url_for('.editStudent', stuId=stuId))
    return render_template('editStudent.html', Permission=Permission, form=form, stu=stu, schdirtea=schdirtea,
                           schdirteaform=schdirteaform)


# 单条删除学生用户信息
@main.route('/student_delete', methods=['GET', 'POST'])
@login_required
def student_delete():
    if current_user.can(Permission.STU_INTERN_MANAGE):
        stuId = request.form.get('stuId')
        print('stuId=', stuId)
        stu = Student.query.filter_by(stuId=stuId).first()
        journal = Journal.query.filter_by(stuId=stuId).all()
        intern = InternshipInfor.query.filter_by(stuId=stuId).all()
        stea = SchDirTea.query.filter_by(stuId=stuId).all()
        ctea = ComDirTea.query.filter_by(stuId=stuId).all()
        try:
            for tea in ctea:
                db.session.delete(tea)
            for tea in stea:
                db.session.delete(tea)
            for jour in journal:
                db.session.delete(jour)
            for i in intern:
                summary = Summary.query.filter_by(internId=i.Id).all()
                for sum in summary:
                    db.session.delete(sum)
                db.session.delete(i)
            db.session.delete(stu)
            db.session.commit()
            flash('删除成功')
            return redirect(url_for('.stuUserList'))
        except Exception as e:
            print('单条删除学生用户：', e)
            db.session.rollback()
            flash('删除失败，请重试！')
            return redirect(url_for('.stuUserList'))
    else:
        return redirect('/')


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
    if not current_user.can(Permission.TEA_INFOR_MANAGE):
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
    if request.method == "POST" and current_user.can(Permission.TEA_INFOR_MANAGE):
        isexport = request.form.get('isexport')
        if isexport:
            file_path = excel_export(excel_export_teaUser, teacher)
            return export_download(file_path)
    return render_template('teaUserList.html', pagination=pagination, form=form, Permission=Permission,
                           teacher=teacher)


# 添加教师用户
@main.route('/addTeacher', methods=['GET', 'POST'])
@login_required
def addTeacher():
    # 非管理员,不能进入
    if not current_user.can(Permission.TEA_INFOR_MANAGE):
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
    if not current_user.can(Permission.PERMIS_MANAGE):
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    pagination = Role.query.paginate(page, per_page=8, error_out=False)
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
        if form.INTERNCOMPANY_LIST.data:
            a = eval(form.INTERNCOMPANY_LIST.description) | a
            print('8')
        if form.STU_INTERN_LIST.data:
            a = eval(form.STU_INTERN_LIST.description) | a
        if form.STU_INTERN_SEARCH.data:
            a = eval(form.STU_INTERN_SEARCH.description) | a
        if form.STU_INTERN_EDIT.data:
            a = eval(form.STU_INTERN_EDIT.description) | a
        if form.STU_INTERN_CHECK.data:
            a = eval(form.STU_INTERN_CHECK.description) | a
        if form.STU_JOUR_SEARCH.data:
            a = eval(form.STU_JOUR_SEARCH.description) | a
        if form.STU_JOUR_EDIT.data:
            a = eval(form.STU_JOUR_EDIT.description) | a
        if form.STU_JOUR_CHECK.data:
            a = eval(form.STU_JOUR_CHECK.description) | a
        if form.STU_SUM_SEARCH.data:
            a = eval(form.STU_SUM_SEARCH.description) | a
        if form.STU_SUM_EDIT.data:
            a = eval(form.STU_SUM_EDIT.description) | a
        if form.STU_SUM_SCO_CHECK.data:
            a = eval(form.STU_SUM_SCO_CHECK.description) | a
        if form.STU_INTERN_MANAGE.data:
            a = eval(form.STU_INTERN_MANAGE.description) | a
        if form.TEA_INFOR_MANAGE.data:
            a = eval(form.TEA_INFOR_MANAGE.description) | a
        if form.PERMIS_MANAGE.data:
            a = eval(form.PERMIS_MANAGE.description) | a
        if form.SELECT_MANAGE.data:
            a = eval(form.SELECT_MANAGE.description) | a
        if form.UPLOAD_VISIT.data:
            a = eval(form.UPLOAD_VISIT.description) | a
        per = hex(a)
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
        if form.INTERNCOMPANY_LIST.data:
            a = eval(form.INTERNCOMPANY_LIST.description) | a
            print('8')
        if form.STU_INTERN_LIST.data:
            a = eval(form.STU_INTERN_LIST.description) | a
        if form.STU_INTERN_SEARCH.data:
            a = eval(form.STU_INTERN_SEARCH.description) | a
        if form.STU_INTERN_EDIT.data:
            a = eval(form.STU_INTERN_EDIT.description) | a
        if form.STU_INTERN_CHECK.data:
            a = eval(form.STU_INTERN_CHECK.description) | a
        if form.STU_JOUR_SEARCH.data:
            a = eval(form.STU_JOUR_SEARCH.description) | a
        if form.STU_JOUR_EDIT.data:
            a = eval(form.STU_JOUR_EDIT.description) | a
        if form.STU_JOUR_CHECK.data:
            a = eval(form.STU_JOUR_CHECK.description) | a
        if form.STU_SUM_SEARCH.data:
            a = eval(form.STU_SUM_SEARCH.description) | a
        if form.STU_SUM_EDIT.data:
            a = eval(form.STU_SUM_EDIT.description) | a
        if form.STU_SUM_SCO_CHECK.data:
            a = eval(form.STU_SUM_SCO_CHECK.description) | a
        if form.STU_INTERN_MANAGE.data:
            a = eval(form.STU_INTERN_MANAGE.description) | a
        if form.TEA_INFOR_MANAGE.data:
            a = eval(form.TEA_INFOR_MANAGE.description) | a
        if form.PERMIS_MANAGE.data:
            a = eval(form.PERMIS_MANAGE.description) | a
        if form.SELECT_MANAGE.data:
            a = eval(form.SELECT_MANAGE.description) | a
        if form.UPLOAD_VISIT.data:
            a = eval(form.UPLOAD_VISIT.description) | a
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
            com = ComInfor.query.filter_by(comProvince=session['city'])

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
                if current_user.can(Permission.COM_INFOR_EDIT):
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor WHERE comCheck=2')
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
                com = com.filter_by(comProvince=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor WHERE comCheck=2')
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
                com = com.filter_by(comProvince=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor WHERE comCheck=2')
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
                com = com.filter_by(comProvince=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor WHERE comCheck=2')
        else:
            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    com = ComInfor.query.order_by(ComInfor.comDate.desc())
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor')
                    print('hi')
                else:
                    com = ComInfor.query.filter_by(comCheck=2).order_by(ComInfor.comDate.desc())
                    citys = db.session.execute('select DISTINCT comProvince from ComInfor WHERE comCheck=2')
            else:
                com = ComInfor.query.filter(ComInfor.comCheck != 2).order_by(ComInfor.comDate.desc())
                citys = db.session.execute('select DISTINCT comProvince from ComInfor WHERE comCheck!=2')
        if not flag:
            com = com.filter(ComInfor.comCheck != 2)
            citys = db.session.execute('select DISTINCT comProvince from ComInfor WHERE comCheck!=2')
    except Exception as e:
        print('组合筛选：', e)
    # 生成筛选项
    for c in citys:
        city[i] = c.comProvince
        i = i + 1
    return com


# 筛选项和组合查询,总结与成果返回的intern已经join了Student
# 总结与成果返回的intern已经join了Student，outerjoin了summary
# 日志返回的intern已经join了Student，Journal
# flag=0实习信息，flag=1实习日志，flag=2实习成果
def create_intern_filter(grade, major, classes, flag):
    # 更新筛选项
    if request.args.get('grade') is not None:
        session['grade'] = request.args.get('grade')

    if request.args.get('major') is not None:
        session['major'] = request.args.get('major')

    if request.args.get('classes') is not None:
        session['classes'] = request.args.get('classes')

    if request.args.get('internStatus') is not None:
        session['internStatus'] = request.args.get('internStatus')

    if request.args.get('checkStatus') is not None:
        session['checkStatus'] = request.args.get('checkStatus')

    i = 0
    j = 0
    k = 0
    # 组合查询 *_*
    try:
        if session.get('grade') is not None:
            intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).filter(
                Student.grade == session['grade'])

            if session.get('major') is not None:
                intern = intern.filter(Student.major == session['major'])

            if session.get('classes') is not None:
                intern = intern.filter(Student.classes == session['classes'])

            if session.get('internStatus') is not None:
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])

            if session.get('checkStatus') is not None:
                if flag == 2:
                    intern = intern.outerjoin(Summary, Summary.internId == InternshipInfor.Id).filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.join(Journal, InternshipInfor.Id == Journal.internId).filter_by(
                        jourCheck=session['checkStatus'])

        elif session.get('major') is not None:
            intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).filter(
                Student.major == session['major'])

            if session.get('grade') is not None:
                intern = intern.filter(Student.grade == session['grade'])

            if session.get('classes') is not None:
                intern = intern.filter_by(classes=session['classes'])

            if session.get('internStatus') is not None:
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])

            if session.get('checkStatus') is not None:
                if flag == 2:
                    intern = intern.outerjoin(Summary, Summary.internId == InternshipInfor.Id).filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor, InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.join(Journal, InternshipInfor.Id == Journal.internId).filter_by(
                        jourCheck=session['checkStatus'])

        elif session.get('classes') is not None:
            intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).filter(
                Student.classes == session['classes'])

            if session.get('grade') is not None:
                intern = intern.filter(Student.grade == session['grade'])

            if session.get('major') is not None:
                intern = intern.filter(Student.major == session['major'])

            if session.get('internStatus') is not None:
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])

            if session.get('checkStatus') is not None:
                if flag == 2:
                    intern = intern.outerjoin(Summary, Summary.internId == InternshipInfor.Id).filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.join(Journal, InternshipInfor.Id == Journal.internId).filter_by(
                        jourCheck=session['checkStatus'])

        elif session.get('internStatus') is not None:

            intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).filter(
                InternshipInfor.internStatus == session['internStatus'])

            if session.get('classes') is not None:
                intern = intern.filter(Student.classes == session['classes'])

            if session.get('grade') is not None:
                intern = intern.filter(Student.grade == session['grade'])

            if session.get('major') is not None:
                intern = intern.filter(Student.major == session['major'])

            if session.get('checkStatus') is not None:
                if flag == 2:
                    intern = intern.outerjoin(Summary, Summary.internId == InternshipInfor.Id).filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.join(Journal, InternshipInfor.Id == Journal.internId).filter_by(
                        jourCheck=session['checkStatus'])

        elif session.get('checkStatus') is not None:
            print('checkStatus')
            if flag == 2:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).outerjoin(Summary,
                                                                                                               Summary.internId == InternshipInfor.Id).filter(
                    Summary.sumCheck == session['checkStatus'])
            elif flag == 0:
                intern = InternshipInfor.query.filter(InternshipInfor.internCheck == session['checkStatus']) \
                    .join(Student, Student.stuId == InternshipInfor.stuId)
            else:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(Journal,
                                                                                                          InternshipInfor.Id == Journal.internId).filter_by(
                    jourCheck=session['checkStatus'])

            if session.get('classes') is not None:
                intern = intern.filter(Student.classes == session['classes'])

            if session.get('grade') is not None:
                intern = intern.filter(Student.grade == session['grade'])

            if session.get('major') is not None:
                intern = intern.filter(Student.major == session['major'])

            if session.get('internStatus') is not None:
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])

        else:
            if flag == 0:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId)
            elif flag == 2:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).outerjoin(Summary,
                                                                                                               Summary.internId == InternshipInfor.Id)
            else:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(Journal,
                                                                                                          InternshipInfor.Id == Journal.internId)

    except Exception as e:
        print('组合筛选：', e)
    # 生成筛选项
    grades = db.session.execute(
        'select DISTINCT grade from Grade order by grade desc')
    majors = db.session.execute(
        'select DISTINCT major from Major')
    classess = db.session.execute(
        'select DISTINCT classes from Classes ORDER BY classes')
    for g in grades:
        grade[i] = g.grade
        i = i + 1
    for m in majors:
        major[j] = m.major
        j = j + 1
    for c in classess:
        classes[k] = c.classes
        k = k + 1
    return intern



def summary_init(internId):
    # 初始化Summary表
    db.session.execute('insert into Summary set internId=%s' % internId)
    # 初始化总结成果文件目录
    os.system('mkdir %s/%s' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/visit' % (STORAGE_FOLDER))
    os.system('mkdir %s/%s/attachment' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/summary_doc' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/score_img' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/agreement' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/score_img/comscore' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/score_img/schscore' % (STORAGE_FOLDER, internId))
    return 1

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
        weeks = 0
        # 第1年至 n-1 年的周数累计
        for x in range(end_isoweek - start_isoweek):
            if x == 0:
                weeks = datetime(start_isoyear, 12, 31).isocalendar()[1] - start_isoweek + 1
            else:
                weeks = weeks + datetime(start_isoyear + x, 12, 31).isocalendar()[1]
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
        print(current_user.get_id(), datetime.now(), "初始化日志失败", e)
        flash('初始化日志失败')
        return redirect('/')
    return 1


# 更改实习信息情况下, 初始化并转移日志
# 不要与 journal_init() 重复使用!!
# 在存在日志数据情况下,修改实习[日志]时间,将转移两次时间段中,重复时间段的日志
# 最后删除旧的实习信息和日志
def journal_migrate(internId):
    try:
        db.session.execute('update Journal set internId=%s where internId=%s' % (-int(internId), internId))
        journal_init(internId)
        db.session.execute('update Journal j1, Journal j2 \
            set j1.mon=j2.mon, j1.tue=j2.tue, j1.wed=j2.wed, j1.thu=j2.thu, j1.fri=j2.fri, j1.sat=j2.sat, j1.sun=j2.sun \
            where j1.internId=%s and j2.internId=%s and j1.isoweek=j2.isoweek and j1.isoyear=j2.isoyear' \
                           % (internId, -int(internId)))
        db.session.execute('delete from Journal where internId=%s' % -int(internId))
    except Exception as e:
        db.session.rollback()
        print(current_user.get_id(), datetime.now(), "初始化并转移日志失败", e)
        flash('初始化并转移日志失败')
        return redirect('/')
    return 1


def update_iso():
    jourlist = Journal.query.all()
    for jour in jourlist:
        start = jour.workStart
        jourId = jour.Id
        db.session.execute('update Journal set isoweek=%s, isoyear=%s where Id=%s' % (
            start.isocalendar()[1], start.isocalendar()[0], jourId))
    return 1


# 学生用户筛选项的生成，组合查询,更新筛选项
# 返回的学生用户信息查询结果stu，筛选项生成在字grade，major，classes中，
def create_stu_filter(grade, major, classes):
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
            stu = Student.query.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])

            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])

        elif session.get('major') is not None:
            stu = Student.query.filter_by(major=session['major'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])

            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])

        elif session.get('classes') is not None:
            stu = Student.query.filter_by(classes=session['classes'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])


        elif session.get('sex') is not None:
            stu = Student.query.filter_by(sex=session['sex'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])

        else:
            stu = Student.query.order_by(Student.grade.asc())

        grades = db.session.execute('select DISTINCT grade from Grade order by grade desc')
        majors = db.session.execute('select DISTINCT major from Major')
        classess = db.session.execute('select DISTINCT classes from Classes ORDER BY classes')
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


# ---------------Excel表格导入导出-----------------------------------------------

# Excel文档列名的模板. 导入和导出
# 实习信息表
excel_export_intern = OrderedDict((('stuId', '学号'), ('stuName', '姓名'), ('comName', '企业名称'), ('address', '地址'),
                                   ('internCheck', '审核状态'), ('internStatus', '实习状态'), ('start', '开始日期'),
                                   ('end', '结束日期'), ('task', '任务'), ('teaName', '审核教师'), ('opinion', '审核意见'),
                                   ('icheckTime', '审核时间'), ('steaName', '校内指导老师姓名'), ('steaDuty', '校内指导老师职务'),
                                   ('steaPhone', '校内指导老师电话'), ('steaEmail', '校内指导老师邮箱'), ('cteaName', '企业指导老师姓名'),
                                   ('cteaDuty', '企业指导老师职务'), ('cteaPhone', '企业指导老师电话'), ('cteaEmail', '企业指导老师邮箱')))
excel_import_intern = {'学号': 'stuId', '姓名': 'stuName', '企业编号': 'comId', '地址': 'address', '开始日期': 'start', '结束日期': 'end',
                       '任务': 'task', '企业指导老师姓名': 'cteaName', '企业指导老师职务': 'cteaDuty', '企业指导老师电话': 'cteaPhone', '企业指导老师邮箱': 'cteaEmail'}
# 企业信息表
excel_export_com = OrderedDict((('comId', '企业编号'), ('comName', '企业名称'), ('comBrief', '企业简介'), ('comAddress', '地址'),
                                ('comUrl', '网站'), ('comMon', '营业额'), ('comContact', '联系人'), ('comDate', '录入时间'),
                                ('comProject', '企业项目'), ('comStaff', '员工人数'), ('comPhone', '电话'), ('comEmail', '邮箱'),
                                ('comFax', '传真'), ('comCheck', '审核状态'), ('students', '实习学生人数')))
excel_import_com = {'企业名称': 'comName', '企业简介': 'comBrief', '地址': 'comAddress', '网站': 'comUrl', '营业额': 'comMon',
                    '联系人': 'comContact', '录入时间': 'comDate', '企业项目': 'comProject', '员工人数': 'comStaff', '电话': 'comPhone',
                    '邮箱': 'comEmail', '传真': 'comFax'}

# 日志表
# 实习详情
excel_export_journal_internDetail =  OrderedDict((('stuId', '学号'), ('stuName', '姓名'), ('comName', '企业名称'),('major','专业班级'), ('start','实习期间')))
# 日志详情
excel_export_journal_log =  OrderedDict((('weekNo','第N周'), ('workStart','工作时间'), ('mon','周一'), ('tue','周二'), ('wed','周三'), ('thu','周四'), ('fri','周五'), ('sat','周六'), ('sun','周日')))

excel_import_journal = {'第N周':'weekNo', '周一':'mon', '周二':'tue', '周三':'wed', '周四':'thu', '周五':'fri', '周六':'sat', '周日':'sun'}


# 学生用户列表
excel_export_stuUser = OrderedDict((('stuId', '学号'), ('stuName', '姓名'), ('sex', '性别'), ('institutes', '院系'),
                                    ('grade', '年级'), ('major', '专业'), ('classes', '班级')))

excel_import_stuUser = {'学号': 'stuId', '姓名': 'stuName', '性别': 'sex', '年级': 'grade', '专业': 'major', '班级': 'classes',
                        '院系': 'institutes'}

# 教师用户列表
excel_export_teaUser = OrderedDict((('teaId', '教工号'), ('teaName', '姓名'), ('teaSex', '性别'), ('roleId', '系统角色')))

excel_import_teaUser = {'教工号': 'teaId', '姓名': 'teaName', '性别': 'teaSex', '系统角色': 'roleId'}

IMPORT_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/xls_import')
EXPORT_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/xls_export')
IMPORT_TEMPLATE_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/import_template')
EXPORT_ALL_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/all_export')


# 可加上成果的上传文件格式限制
# ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])


def allowed_file(filename, secure_postfix):
    return '.' in filename and filename.rsplit('.', 1)[1] in secure_postfix

# 下载导出文件
def export_download(file_path):
    template_dict = {'internlist':'实习信息导出表', 'comlist':'企业信息导出表', 'stuUserList':'学生用户信息导出表', 'teaUserList':'教师用户信息导出表', 'journalList':'日志记录导出表'}
    file_name = os.path.basename(file_path)
    index = file_name.split('_')[0]
    if index in template_dict.keys():
        file_attachname = template_dict[index] + '_%s.xls' % datetime.now().date()
    # attachment_finaname为下载时,提供的默认文件名
    return send_file(file_path, as_attachment=True, attachment_filename=file_attachname.encode('utf-8')) 


# 导出日志表
def journal_export(internIdList):
    template_A = excel_export_journal_internDetail
    template_B = excel_export_journal_log
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet 1', cell_overwrite_ok=True)
    row = 0
    for internId in internIdList:
        intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(ComInfor, ComInfor.comId == InternshipInfor.comId).add_columns(InternshipInfor.stuId, InternshipInfor.start, InternshipInfor.end, Student.stuName, Student.major, Student.classes, ComInfor.comName).filter(InternshipInfor.Id == internId).first()
        journal = Journal.query.filter(Journal.internId == internId).all()
        # 实习详情, 一次写两行
        for col, colname in zip(range(len(template_A)), template_A):
            ws.write(row, col, template_A.get(colname))
            if colname in ['stuId']:
                ws.write(row+1, col, int(getattr(intern, colname)))
            elif colname in ['stuName', 'comName']:
                ws.write(row+1, col, str(getattr(intern, colname)))
            elif colname in ['major']:
                ws.write(row+1, col, ((getattr(intern, colname) + str(getattr(intern,'classes')) + '班')))
            elif colname in ['start']:
                ws.write(row+1, col, (str(getattr(intern, colname)) + ' 至 ' + str(getattr(intern,'end')) ))
        # 空一行
        row = row + 3
        # 日志记录
        for col, colname in zip(range(len(template_B)), template_B):
            ws.write(row, col, template_B.get(colname))
        for journal_temp in journal:
            row = row + 1
            for col, colname in zip(range(len(template_B)), template_B):
                if colname in ['weekNo']:
                    ws.write(row, col, int(getattr(journal_temp, colname)))
                elif colname in ['workStart']:
                    ws.write(row, col, (str(getattr(journal_temp, colname)) + ' 至 ' + str(getattr(journal_temp, 'workEnd'))))
                else:
                    ws.write(row, col, str(getattr(journal_temp, colname)))
            # for journal_temp in journal:
            #     row = row + 1
            #     if colname in ['weekNo']:
            #         ws.write(row, col, int(getattr(journal_temp, colname)))
            #     elif colname in ['workStart']:
            #         ws.write(row, col, (str(getattr(journal_temp, colname)) + ' 至 ' + str(getattr(journal_temp, 'workEnd'))))
            #     else:
            #         ws.write(row, col, str(getattr(journal_temp, colname)))
        # 空两行
        row = row + 3
    file_name = 'journalList_export_%s' % random.randint(1,100)
    file_path = os.path.join(EXPORT_FOLDER, file_name)
    wb.save(file_path)
    return file_path 


# 导出Excel, 多个指导老师合并在一个单元格上
def multiDirTea_dict(tb_name):
    if tb_name in ['SchDirTea', 'ComDirTea']:
        multiDirTea = db.session.execute(
            'select * from %s where stuId in (select stuId from %s group by stuId having count(stuId) > 1)' % (
                tb_name, tb_name))
        multiDirTea_dict = {}
        # 校内导师
        if tb_name == 'SchDirTea':
            for x in multiDirTea:
                # if not multiDirTea_dict[x.stuId]:
                if not multiDirTea_dict.get(x.stuId):
                    multiDirTea_dict[x.stuId] = {'steaName': x.steaName, 'steaDuty': x.steaDuty,
                                                 'steaEmail': x.steaEmail, 'steaPhone': x.steaPhone}
                    for xx in multiDirTea_dict[x.stuId]:
                        if multiDirTea_dict[x.stuId].get(xx) is None:
                            multiDirTea_dict[x.stuId][xx] = '未知'
                else:
                    multiDirTea_dict[x.stuId] = { \
                        'steaName': multiDirTea_dict[x.stuId]['steaName'] + '/%s' % x.steaName, \
                        'steaDuty': multiDirTea_dict[x.stuId]['steaDuty'] + '/%s' % x.steaDuty, \
                        'steaEmail': multiDirTea_dict[x.stuId]['steaEmail'] + '/%s' % x.steaEmail, \
                        'steaPhone': multiDirTea_dict[x.stuId]['steaPhone'] + '/%s' % x.steaPhone \
                        }
        # 企业导师
        elif tb_name == 'ComDirTea':
            for x in multiDirTea:
                if not multiDirTea_dict.get(x.stuId):
                    multiDirTea_dict[x.stuId] = {'cteaName': x.cteaName, 'cteaDuty': x.cteaDuty,
                                                 'cteaEmail': x.cteaEmail, 'cteaPhone': x.cteaPhone}
                    for xx in multiDirTea_dict[x.stuId]:
                        if multiDirTea_dict[x.stuId].get(xx) is None:
                            multiDirTea_dict[x.stuId][xx] = '未知'

                else:
                    multiDirTea_dict[x.stuId] = { \
                        'cteaName': multiDirTea_dict[x.stuId]['cteaName'] + '/%s' % x.cteaName, \
                        'cteaDuty': multiDirTea_dict[x.stuId]['cteaDuty'] + '/%s' % x.cteaDuty, \
                        'cteaEmail': multiDirTea_dict[x.stuId]['cteaEmail'] + '/%s' % x.cteaEmail, \
                        'cteaPhone': multiDirTea_dict[x.stuId]['cteaPhone'] + '/%s' % x.cteaPhone \
                        }
        return multiDirTea_dict



# 导出Excel
# 实习列表传入Basequery对象,企业列表传入list结果对象
def excel_export(template, data):
    # 实习列表再处理
    if template == excel_export_intern:
        multiSchTea = multiDirTea_dict('SchDirTea')
        multiComTea = multiDirTea_dict('ComDirTea')
        data = data.outerjoin(SchDirTea, SchDirTea.stuId == InternshipInfor.stuId).outerjoin(ComDirTea, and_(
            ComDirTea.comId == InternshipInfor.comId, ComDirTea.stuId == InternshipInfor.stuId)) \
            .add_columns(SchDirTea.steaName, SchDirTea.steaDuty, SchDirTea.steaPhone, SchDirTea.steaEmail,
                         ComDirTea.cteaName, ComDirTea.cteaDuty, ComDirTea.cteaPhone, ComDirTea.cteaEmail).group_by(
            InternshipInfor.Id).all()

    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet 1', cell_overwrite_ok=True)
    # 列名
    cols_list = []
    for col, colname in zip(range(len(template)), template):
        ws.write(0, col, template.get(colname))
        cols_list.append(colname)
    # 数据
    for row, xdata in zip(range(len(data)), data):
        for col, colname in zip(range(len(template)), template):
            # 根据输出到Excel的类型和内容做判断
            if colname in ['internCheck', 'comCheck']:
                if getattr(xdata, colname) == 0:
                    ws.write(row + 1, col, '待审核')
                elif getattr(xdata, colname) == 1:
                    ws.write(row + 1, col, '被退回修改')
                else:
                    ws.write(row + 1, col, '已审核')
            elif colname in ['internStatus']:
                if getattr(xdata, colname) == 0:
                    ws.write(row + 1, col, '待实习')
                elif getattr(xdata, colname) == 1:
                    ws.write(row + 1, col, '实习中')
                else:
                    ws.write(row + 1, col, '实习结束')
            # 日期时间不用str的话, 返回的会是个float
            # elif colname in ['start', 'end', 'icheckTime', 'comDate']:
            #     if getattr(xdata, colname):
            #         ws.write(row + 1, col, str(getattr(xdata, colname)))
            elif colname in ['classes']:
                ws.write(row + 1, col, str(getattr(xdata, colname)) + '班')
            elif colname in ['roleId']:
                if getattr(xdata, colname) == 3:
                    ws.write(row + 1, col, '管理员')
                elif getattr(xdata, colname) == 2:
                    ws.write(row + 1, col, '审核老师')
                elif getattr(xdata, colname) == 1:
                    ws.write(row + 1, col, '普通老师')
            else:
                if getattr(xdata, colname):
                    ws.write(row + 1, col, str(getattr(xdata, colname)))
        # 若一学生存在多个导师
        if template == excel_export_intern:
            if xdata.stuId in multiSchTea.keys():
                ws.write(row + 1, cols_list.index('steaName'), multiSchTea[xdata.stuId]['steaName'])
                ws.write(row + 1, cols_list.index('steaPhone'), multiSchTea[xdata.stuId]['steaPhone'])
                ws.write(row + 1, cols_list.index('steaDuty'), multiSchTea[xdata.stuId]['steaDuty'])
                ws.write(row + 1, cols_list.index('steaEmail'), multiSchTea[xdata.stuId]['steaEmail'])
            if xdata.stuId in multiComTea.keys():
                ws.write(row + 1, cols_list.index('cteaName'), multiComTea[xdata.stuId]['cteaName'])
                ws.write(row + 1, cols_list.index('cteaPhone'), multiComTea[xdata.stuId]['cteaPhone'])
                ws.write(row + 1, cols_list.index('cteaDuty'), multiComTea[xdata.stuId]['cteaDuty'])
                ws.write(row + 1, cols_list.index('cteaEmail'), multiComTea[xdata.stuId]['cteaEmail'])
    # 每个模板最多保存100份导出临时文件
    if template == excel_export_intern:
        file_name = 'internlist_export_%s.xls' % random.randint(1, 99)
    elif template == excel_export_com:
        file_name = 'comlist_export_%s.xls' % random.randint(1, 99)
    elif template == excel_export_stuUser:
        file_name = 'stuUserList_export_%s.xls' % random.randint(1, 99)
    elif template == excel_export_teaUser:
        file_name = 'teaUserList_export_%s.xls' % random.randint(1, 99)
    file_path = os.path.join(EXPORT_FOLDER, file_name)
    wb.save(file_path)
    return file_path


# 导出所有实习资料
@update_intern_internStatus
def export_all():
    # 根目录
    root_path = os.path.join(EXPORT_ALL_FOLDER, str(datetime.now().timestamp()))
    root_path_2 = os.path.join(root_path, '实习管理系统批量导出_%s' % datetime.now().date())
    file_list = []
    intern_org = InternshipInfor.query.join(Student, Student.stuId==InternshipInfor.stuId) \
        .join(ComInfor, ComInfor.comId==InternshipInfor.comId) \
        .outerjoin(Teacher, Teacher.teaId==InternshipInfor.icheckTeaId) \
        .filter(InternshipInfor.internStatus==2, InternshipInfor.internCheck==2) \
        .add_columns(InternshipInfor.Id, InternshipInfor.stuId, InternshipInfor.internCheck, InternshipInfor.internStatus, InternshipInfor.start, InternshipInfor.end, InternshipInfor.task, InternshipInfor.opinion, InternshipInfor.icheckTime, Student.stuName, Student.grade, Student.major, ComInfor.comName, InternshipInfor.address, Teacher.teaName)
    internlist = intern_org.all()
    for intern in internlist:
        x_grade = intern.grade
        x_major = intern.major
        x_stuName = intern.stuName
        x_stuId = intern.stuId
        x_comName = intern.comName
        intern_path = excel_export(excel_export_intern, intern_org.filter(InternshipInfor.Id==intern.Id))
        journal_path = journal_export([intern.Id])
        storage_path = os.path.join(STORAGE_FOLDER, str(intern.Id))
        path_group = {
            'grade': str(x_grade),
            'major': x_major,
            'stuName': x_stuName,
            'stuId': x_stuId,
            'comName': x_comName,
            'intern_path': intern_path,
            'journal_path': journal_path,
            'storage_path': storage_path
        }
        file_list.append(path_group)
    # 建立文件
    for x in file_list:
        root_path_3 = os.path.join(root_path_2, x['grade'], x['major'], x['stuId']+'_'+x['stuName'], x['comName'])
        print (root_path_3)
        os.system('mkdir -p %s' % root_path_3)
        os.system('cp -r %s/* %s %s %s' % (x['storage_path'], x['intern_path'], x['journal_path'], root_path_3))
        # 更改中文名
        os.system('mv %s/summary_doc %s/总结文档' % (root_path_3, root_path_3))
        os.system('mv %s/attachment %s/附件' % (root_path_3, root_path_3))
        os.system('mv %s/score_img/comscore %s/score_img/企业评分' % (root_path_3, root_path_3))
        os.system('mv %s/score_img/schscore %s/score_img/校内评分' % (root_path_3, root_path_3))
        os.system('mv %s/score_img %s/评分' % (root_path_3, root_path_3))
        os.system('mv %s/internlist* %s/%s_实习信息.xls' % (root_path_3, root_path_3, x['comName']))
        os.system('mv %s/journalList* %s/%s_实习日志.xls' % (root_path_3, root_path_3, x['comName']))
    # 打包zip文件
    zip_folder = os.path.basename(root_path_2)
    zip_file = '%s.zip' % zip_folder
    zip_path = os.path.join(root_path, zip_file)
    os.system('cd %s; zip -0r %s %s' %(root_path, zip_file, zip_folder))
    # return zip_path
    file_attachname = os.path.basename(root_path_2)+'.zip'
    return send_file(zip_path, as_attachment=True, attachment_filename=file_attachname.encode('utf-8')) 

@main.route('/export_all_page', methods=['GET', 'POST'])
def export_all_page():
    if current_user.can(Permission.STU_INTERN_SEARCH) and current_user.can(Permission.STU_JOUR_SEARCH) and current_user.can(Permission.STU_SUM_SEARCH):
        return export_all()


# 导入excel表, 检查数据是否完整或出错
EXCEL_IMPORT_CHECK_STUINTERNLIST = ['stuId', 'stuName', 'comId', 'start', 'end']
EXCEL_IMPORT_CHECK_INTERNCOMPANY = ['comName', 'comAddress', 'comProject', 'comPhone', 'comEmail']
EXCEL_IMPORT_CHECK_STUUSERLIST = ['stuId', 'stuName', 'grade', 'classes', 'major', 'sex']
EXCEL_IMPORT_CHECK_JOURNAL = ['weekNo']
# 教师工号可为空
EXCEL_IMPORT_CHECK_TEAUSERLIST = ['teaName', 'teaSex', 'teaId']


# 导入Excel
def excel_import(file, template, check_template):
    book = xlrd.open_workbook(file)
    data = []
    for sheet in range(book.nsheets):
        sh = book.sheet_by_index(sheet)
        col_name = []
        for col in range(sh.ncols):
            # 如果template里面没找到对应的key,则为None. 所在列的数据也不会录入
            temp = template.get(sh.cell_value(rowx=0, colx=col))
            if temp in excel_import_intern.values() and temp in col_name:
                flash('导入失败: 部分信息有重复, 请使用提供的模板来写入数据')
                print('导入失败: 部分信息有重复, 请使用提供的模板来写入数据')
                return False
            col_name.append(temp)
        # 检查列名是否有错
        for x in check_template:
            # print ('template[x]', template[x])
            if x not in col_name:
                flash('导入失败: 部分必需信息缺失,请使用提供的模板来写入数据')
                print('导入失败: 部分必需信息缺失,请使用提供的模板来写入数据')
                # return redirect('/')
                return False
        for row in range(sh.nrows - 1):
            # 导入数据
            data_row = {}
            for col in range(sh.ncols):
                if col_name[col]:
                    # excel的日期类型数据会返回float, 此处修改为string
                    if col_name[col] == 'start' or col_name[col] == 'end':
                        data_row[col_name[col]] = datetime(*xlrd.xldate_as_tuple(sh.cell_value(rowx=row + 1, colx=col), book.datemode)).date()
                        # data_row[col_name[col]] = str(datetime(*xlrd.xldate_as_tuple(sh.cell_value(rowx=row + 1, colx=col), book.datemode)).date())
                    else:
                        data_row[col_name[col]] = str(sh.cell_value(rowx=row + 1, colx=col))
            # 检查开始时间是否比结束世界要早
            if template == excel_import_intern:
                if data_row['start'] > data_row['end']:
                    flash('导入失败:有不完整或格式不对的数据,请修改后再导入')
                    print('导入失败:有不完整或格式不对的数据,请修改后再导入')
                    return False
            # 检查每行的必要数据是否存在
            for x in check_template:
                # excel的空白默认为6个' '?
                if x not in ['start', 'end']:
                    if data_row.get(x).strip() is '':
                        flash('导入失败:有不完整或格式不对的数据,请修改后再导入')
                        print('导入失败:有不完整或格式不对的数据,请修改后再导入')
                        return False
            data.append(data_row)
    return data


# 已合并到excel_import()
def excel_import_check(data, template):
    if template in [EXCEL_IMPORT_CHECK_STUINTERNLIST, EXCEL_IMPORT_CHECK_INTERNCOMPANY, EXCEL_IMPORT_CHECK_STUUSERLIST, EXCEL_IMPORT_CHECK_JOURNAL, EXCEL_IMPORT_CHECK_TEAUSERLIST]:
        # 判断属性是否齐全
        for x in template:
            if x not in data[0].keys():
                flash('导入失败: 部分必需信息缺失,请使用提供的模板来写入数据')
                print('导入失败: 部分必需信息缺失,请使用提供的模板来写入数据')
                return redirect('/')
        for xdata, col in zip(data, range(len(data))):
            # 判断必需数据是否完整
            for x in template:
                if xdata[x] is None:
                # if str(xdata[x]) is (None or ''):
                    # 第几行这里有误
                    flash('导入失败:第%s行有不完整或格式不对的数据,请修改后再导入' % col + 1)
                    print('导入失败:第%s行有不完整或格式不对的数据,请修改后再导入' % col + 1)
                    return redirect('/')

# 导入的Excel中, 统一将长串的float类型改为str
# 适用于学号,电话号码
def float2str(float_id):
    print (float_id)
    if re.match(r'.*\..*', float_id):
        str_id = str(float_id[:-2])
        print ('1', str_id)
    else:
        str_id = float_id
        print ('2', str_id)
    return str_id


# excel导入页面处理
@main.route('/excel_importpage', methods=['GET', 'POST'])
def excel_importpage():
    from_url = request.args.get('from_url')
    # 当from_url=='xJournal'时, 需要用到InernId
    internId = request.args.get('internId')
    temp_dict = {
        'stuInternList':
            {'file_name':'stuInternList_import_template.xls', 'attach_name':'实习信息导入模板.xls'}, 
        'xJournal':
            {'file_name':'xJournal_import_template.xls', 'attach_name': '日志导入模板.xls'}, 
        'interncompany':
            {'file_name': 'interncompany_import_template.xls', 'attach_name': '企业导入模板.xls'}, 
        'teaUserList':
            {'file_name':'teaUserList_import_template.xls', 'attach_name':'教师用户信息导入模板.xls'}, 
        'stuUserList': 
            {'file_name': 'stuUserList_import_template.xls', 'attach_name':'学生用户信息导入模板.xls'}
    }
    if from_url == 'stuInternList':
        permission = current_user.can(Permission.STU_INTERN_CHECK)
    elif from_url == 'interncompany':
        permission = current_user.can(Permission.COM_INFOR_EDIT)
    elif from_url == 'stuUserList':
        permission = current_user.can(Permission.STU_INTERN_MANAGE)
    elif from_url == 'teaUserList':
        permission = current_user.can(Permission.TEA_INFOR_MANAGE)
    elif from_url == 'xJournal':
        # 默认角色下, 只有学生个人和管理员才能编辑日志
        permission = (current_user.roleId == 0) or curent_user.can(Permission.STU_JOUR_EDIT)
    if not permission:
        flash('非法操作')
        return redirect('/')
    if request.method == 'POST':
        # 模板下载
        import_template_download = request.form.get('import_template_download')
        now = datetime.now().date()
        if import_template_download:
            file_path = os.path.join(IMPORT_TEMPLATE_FOLDER, temp_dict[from_url]['file_name'])
            attach_name = temp_dict[from_url]['attach_name']
            return send_file(file_path, as_attachment=True, attachment_filename=attach_name.encode('utf-8'))
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
        if file and allowed_file(file.filename, ['xls', 'xlsx']):
            filename = '%s_import_%s.xls' % (from_url, random.randint(1, 99))
            file.save(os.path.join(IMPORT_FOLDER, filename))
            # 上传成功,开始导入
            try:
                if from_url == "stuInternList":
                    internlist = excel_import(os.path.join(IMPORT_FOLDER, filename), excel_import_intern, EXCEL_IMPORT_CHECK_STUINTERNLIST)
                    if internlist is False:
                        return redirect('/')
                    for intern, col in zip(internlist, range(len(internlist))):
                        internId = int(InternshipInfor.query.order_by(InternshipInfor.Id.desc()).first().Id) + 1
                        start = intern['start']
                        end = intern['end']
                        # 实习状态
                        if now < start:
                            intern['internStatus'] = 0  # 待实习
                        elif now >= start and now <= end:
                            intern['internStatus'] = 1  # 实习中
                        else:
                            intern['internStatus'] = 2  # 实习结束
                        # 因导入本身需要审核权限, 所以这里自动通过审核
                        internship = InternshipInfor(
                            stuId = float2str(intern['stuId']),
                            address=intern['address'],
                            start=start,
                            end=end,
                            task=intern['task'],
                            comId=intern['comId'][:-2],
                            internStatus=intern['internStatus'],
                            internCheck = 2,
                            icheckTime = now
                        )
                        db.session.add(internship)

                        # 添加企业指导老师
                        cteaName_temp = intern['cteaName'].split('/')
                        cteaDuty_temp = intern['cteaDuty'].split('/')
                        cteaPhone_temp = intern['cteaPhone'].split('/')
                        cteaEmail_temp = intern['cteaEmail'].split('/')
                        # len()表示有几位老师, 检查前后数据是否对应
                        assert len(cteaName_temp) == len(cteaDuty_temp) == len(cteaEmail_temp) == len(cteaPhone_temp), '企业指导老师的数据格式有误'
                        for x in range(len(cteaName_temp)):
                            comdirtea = ComDirTea(
                                stuId = intern['stuId'],
                                comId = intern['comId'],
                                cteaName = cteaName_temp[x].strip(), 
                                cteaDuty = cteaDuty_temp[x].strip(), 
                                cteaPhone = float2str(cteaPhone_temp[x].strip()), 
                                cteaEmail = cteaEmail_temp[x].strip()
                            )
                            db.session.add(comdirtea)

                        for x in range(len(intern['cteaName'].split('/'))):
                            intern['cteaName'].split('/')[x]
                        # 增加企业实习人数
                        db.session.execute('update ComInfor set students=students+1 where comId=%s' % str(intern['comId'])[:-2])

                        db.session.commit()
                        # 初始化日志, 总结成果
                        journal_init(internId)
                        summary_init(internId)
                elif from_url == 'xJournal':
                    journalList = excel_import(os.path.join(IMPORT_FOLDER, filename), excel_import_journal, EXCEL_IMPORT_CHECK_JOURNAL)
                    # 检查数据是否缺失,完整或出错
                    if journalList is False:
                        return redirect('/')
                    week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                    today = datetime.now().date()
                    journal_object = Journal.query.filter(Journal.internId==internId).all()
                    for journal, col, jour in zip(journalList, range(len(journalList)), journal_object):
                        if jour.jourCheck == 0 and journal['weekNo']:
                            # if jour.workEnd <= today:
                            #     for x in week:
                            #         if journal[x]:
                            #             db.session.execute('update Journal set %s = "%s" where internId=%s and weekNo=%s' % (x, journal[x], internId,  int(journal['weekNo'].split('.')[0])))
                            # # 当前周时, 只更新当天及其之前的日志
                            # elif jour.workStart <= today:
                            #     for x in range(jour.workStart.isocalendar()[2], today.isocalendar()[2]+1):
                            #         which_day = week[x]
                            #         if journal[which_day]:
                            #             db.session.execute('update Journal set %s = "%s" where internId=%s and weekNo=%s' % (which_day, journal[which_day], internId,  int(journal['weekNo'].split('.')[0])))

                            # 本工作周最后一天
                            if jour.workEnd <= today:
                                week_end = jour.workEnd
                            else:
                                week_end = today
                            for x in range(jour.workStart.isocalendar()[2], week_end.isocalendar()[2]+1):
                                whcih_day = week[x]
                                if journal[which_day]:
                                    db.session.execute('update Journal set %s = "%s" where internId=%s and weekNo=%s' % (which_day, journal[which_day], internId,  int(journal['weekNo'].split('.')[0])))

                elif from_url == 'interncompany':
                    comlist = excel_import(os.path.join(IMPORT_FOLDER, filename), excel_import_com, EXCEL_IMPORT_CHECK_INTERNCOMPANY)
                    if comlist is False:
                        return redirect('/')
                    for com, col in zip(comlist, range(len(comlist))):
                        if current_user.can(Permission.COM_INFOR_CHECK):
                             cominfor = ComInfor(
                                comName=com['comName'],
                                comBrief=com['comBrief'],
                                comAddress=com['comAddress'],
                                comUrl=com['comUrl'],
                                # 使Excel生成的保留一位小数数字,变成保留到个位
                                comMon=str(com['comMon'])[:-2],
                                comContact=com['comContact'],
                                comDate = now,
                                comProject=com['comProject'],
                                comStaff=com['comStaff'],
                                comPhone=com['comPhone'],
                                comEmail=com['comEmail'],
                                comFax=com['comFax'],
                                comCheck=2
                            )
                        else:
                            cominfor = ComInfor(
                                comName=com['comName'],
                                comBrief=com['comBrief'],
                                comAddress=com['comAddress'],
                                comUrl=com['comUrl'],
                                # 使Excel生成的保留一位小数数字,变成保留到个位
                                comMon=str(com['comMon'])[:-2],
                                comContact=com['comContact'],
                                comDate = now,
                                comProject=com['comProject'],
                                comStaff=com['comStaff'],
                                comPhone=com['comPhone'],
                                comEmail=com['comEmail'],
                                comFax=com['comFax'],
                                comCheck =0
                            )
                        db.session.add(cominfor)

                elif from_url == 'stuUserList':
                    stuUserList = excel_import(os.path.join(IMPORT_FOLDER, filename), excel_import_stuUser, EXCEL_IMPORT_CHECK_STUUSERLIST)
                    if stuUserList is False:
                        return redirect('/')
                    for stuUser, col in zip(stuUserList, range(len(stuUserList))):
                        # 数据规范
                        # 班级取数字, 不要'班'
                        classes = re.findall(r'\d+', stuUser['classes'])[0]
                        # 例'2014级'取'2014'
                        grade = re.findall(r'\d{4}', stuUser['grade'])[0]
                        student = Student(
                            stuId = float2str(stuUser['stuId']),
                            stuName=stuUser['stuName'],
                            major=stuUser['major'],
                            sex=stuUser['sex'],
                            classes=classes,
                            grade=grade,
                            institutes=stuUser['institutes']
                        )
                        db.session.add(student)
                elif from_url == 'teaUserList':
                    teaUserList = excel_import(os.path.join(IMPORT_FOLDER, filename), excel_import_teaUser,EXCEL_IMPORT_CHECK_TEAUSERLIST)
                    if teaUserList is False:
                        return redirect('/')
                    for teaUser, col in zip(teaUserList, range(len(teaUserList))):
                        # 系统角色Id为空, 则默认普通老师
                        roleId = teaUser['roleId']
                        if re.match(r'^\d{1}$', roleId) is None:
                            roleId = '1'
                        teacher = Teacher(
                            teaId=str(teaUser['teaId'])[:-2],
                            teaName=teaUser['teaName'],
                            teaSex=teaUser['teaSex'],
                            roleId=roleId
                        )
                        db.session.add(teacher)
                # 最后提交并跳转到原本的地址
                db.session.commit()
                flash('导入成功')
                if from_url == "xJournal":
                    return redirect(url_for('.%s' % from_url, internId=internId))
                return redirect(url_for('.%s' % from_url))
            except Exception as e:
                flash('导入出现异常')
                print(from_url, '导入出现异常:', e)
                db.session.rollback()
                return redirect('/')
        else:
            flash('请上传正确的Excel文件( .xls和 .xlsx格式)')
            return redirect('/')
    return render_template('excel_import.html', Permission=Permission)


# ---------------实习总结与成果---------------------------------------

STORAGE_FOLDER = os.path.join(os.path.abspath('.'), 'storage')
STATIC_STORAGE='/static/storage'
PDF_FOLDER = os.path.join(os.path.abspath('.'), 'app/static/onlinePDF')


# 返回相对应的存储路径
def storage_cwd(internId, dest):
    if dest in ['score_img', 'summary_doc', 'attachment']:
        file_path = os.path.join(STORAGE_FOLDER, internId, dest)
        return file_path


# 返回相对应的PDF路径
def pdf_cwd(internId, dest):
    if dest in ['summary_doc', 'attachment']:
        file_path = os.path.join(PDF_FOLDER, internId, dest)
        return file_path


# 目录下的文件列表
# 文件名 文件大小 上传时间
# 返回嵌套字典 {'file01':{'fsize':'2MB', 'mtime':'2016-01-01 08:00'}, 'file02':{'fsize':'144KB', 'mtime':'2016-11-01 08:12'}}
def storage_list(internId, dest):
    file_path = storage_cwd(internId, dest)
    # 先判断是否存在该目录
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_list = {}
    for f in os.listdir(file_path):
        fsize = os.path.getsize(os.path.join(file_path, f))
        if f == 'pdf':
            continue
        # 文件大小h.join(file_path, f))/1024
        if fsize < 1024:
            fsize = '0.1KB'
        elif fsize >= 1024 and fsize < 1024 * 1024:
            fsize = '%s' % (fsize / 1024)
            # 仅保留一位小数
            integer = fsize.split('.')[0]
            decimal = fsize.split('.')[1][0]
            fsize = '%s.%sKB' % (integer, decimal)
        elif fsize >= 1024 * 1024:
            fsize = '%s' % (fsize / 1024 / 1024)
            # 仅保留一位小数
            integer = fsize.split('.')[0]
            decimal = fsize.split('.')[1][0]
            fsize = '%s.%sMB' % (integer, decimal)
        # 上传时间
        mtime = datetime.fromtimestamp(os.path.getmtime(os.path.join(file_path, f))).strftime('%Y-%m-%d %H:%M')
        file_list[f] = {'fsize': fsize, 'mtime': mtime}
    return file_list


# 下载文件
# return这个函数,直接弹窗下载
# 总结论文和附件的下载
def storage_download(internId):
    path_dict = {'attachment_download': 'attachment', 'summary_doc_download': 'summary_doc'}
    for x in path_dict:
        file_name = request.form.get(x)
        if file_name:
            file_path = storage_cwd(internId, path_dict[x])
            return send_file(os.path.join(file_path, file_name), as_attachment=True,
                             attachment_filename=file_name.encode('utf-8'))


def storage_upload(internId):
    path_dict = {'attachment_upload': 'attachment', 'summary_doc_upload': 'summary_doc'}
    for x in path_dict:
        file = request.files.get(x)
        if file:
            try:
                filename = file.filename
                dest = path_dict[x]
                file_path = storage_cwd(internId, dest)
                file.save(os.path.join(file_path, filename))
                return True
            except Exception as e:
                print(datetime.now(), '上传文件失败', e)
                return False


# 修改文件后缀名为pdf
# 考虑到文件名前缀带有'.'
def pdf_postfix(file_name):
    index = file_name[::-1].find('.')
    index = -index
    pdf_name = file_name[:index] + 'pdf'
    return pdf_name


# file为初始文件名, 非pdf
def onlinePDF(internId, dest, file):
    if dest in ['summary_doc', 'attachment']:
        if file.split('.')[-1] in ['xls', 'doc', 'docx', 'ppt', 'txt', 'docs', 'xlsx', 'jpg', 'jpeg', 'png']:
            pdf_file = pdf_postfix(file)
            storage_path = os.path.join(storage_cwd(internId, dest), file)
            pdf_path = os.path.join(pdf_cwd(internId, dest), pdf_file)
            if os.path.exists(pdf_path):
                pdf_path = pdf_path[pdf_path.find('/static'):]
            else:
                os.system('unoconv -f pdf -o %s %s' % (pdf_path, storage_path))
                pdf_path = pdf_path[pdf_path.find('/static'):]
            return pdf_path


# 学生实习总结与成果列表
@main.route('/stuSumList', methods=['GET', 'POST'])
@login_required
@update_intern_internStatus
def stuSumList():
    form = searchForm()
    grade = {}
    major = {}
    classes = {}
    page = request.args.get('page', 1, type=int)
    now = datetime.now().date()
    if current_user.roleId == 0:
        stuId = current_user.stuId
        # 消除消息提示
        if session['message']['2'] == 1:
            try:
                db.session.execute('update Student set sumCheck=0 where stuId=%s' % stuId)
                session['message']['2'] = 0
            except Exception as e:
                print('message:', e)
                flash('error!!!')
                return redirect('/')
        student = Student.query.filter_by(stuId=stuId).first()
        internship = InternshipInfor.query.filter_by(stuId=stuId).first()
        # 让添加实习企业 addcominfor 下一步跳转到 addinternship
        if internship is None:
            flash('您还没完成实习信息的填写，请完善相关实习信息！')
            return redirect(url_for('.addcominfor', from_url='stuInternList'))
        else:
            pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(
                Summary, Summary.internId == InternshipInfor.Id) \
                .add_columns(ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start,
                             InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck,
                             Summary.sumScore, Summary.sumCheck) \
                .filter(InternshipInfor.stuId == stuId).order_by(
                func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
            internlist = pagination.items
            return render_template('stuSumList.html', internlist=internlist, Permission=Permission,
                                   student=student, pagination=pagination, form=form,
                                   grade=grade, major=major, classes=classes)
    elif current_user.can(Permission.STU_INTERN_LIST):
        # 函数返回的intern已经join了Student,Summary
        intern = create_intern_filter(grade, major, classes, 2)
        pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
            .filter(InternshipInfor.internCheck == 2, InternshipInfor.internStatus == 2) \
            .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName,
                         InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end,
                         InternshipInfor.internCheck, Summary.sumScore, Summary.sumCheck) \
            .order_by(InternshipInfor.end.desc(), InternshipInfor.internStatus.desc()).paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        return render_template('stuSumList.html', internlist=internlist, Permission=Permission,
                               pagination=pagination, form=form, grade=grade, classes=classes, major=major)
    else:
        flash('非法操作')
        return redirect('/')


# 学生个人实习总结与成果
@main.route('/xSum', methods=['GET', 'POST'])
@login_required
def xSum():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    internId = request.args.get('internId')
    summary = request.args.get('summary')
    attach = request.args.get('attach')
    path = None
    if summary:
        path = onlinePDF(internId, 'summary_doc', summary)
    elif attach:
        path = onlinePDF(internId, 'attachment', attach)
    comId = InternshipInfor.query.filter_by(Id=internId).first().comId
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    now = datetime.now().date()
    student = Student.query.filter_by(stuId=stuId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    summary = Summary.query.filter_by(internId=internId).first()
    summary_doc = storage_list(internId, 'summary_doc')
    attachment = storage_list(internId, 'attachment')
    if request.method == 'POST':
        return storage_download(internId)
    if current_user.roleId == 0:
        return render_template('xSum.html', Permission=Permission, comInfor=comInfor, internship=internship,
                               student=student, summary=summary, attachment=attachment, summary_doc=summary_doc,
                               path=path)
    elif internship.end < now:
        if internship.internCheck == 2:
            return render_template('xSum.html', Permission=Permission, comInfor=comInfor, internship=internship,
                                   student=student, summary=summary, attachment=attachment, summary_doc=summary_doc,
                                   path=path)
        else:
            flash("实习申请需审核后,才能查看总结和成果")
            return redirect(url_for('.xIntern', stuId=stuId, internId=internId))
    else:
        flash('实习尚未结束, 请待实习结束后再查看实习总结和成果')
        # from_url = request.args.get('from_url')
        # return redirect(url_for('.%s' % from_url, internId=internId, stuId=student.stuId))
        return redirect(url_for('.index'))



# 学生个人实习总结与成果的"文件管理"!
@main.route('/xSum_fileManager', methods=['GET', 'POST'])
@login_required
def xSum_fileManager():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    internId = request.args.get('internId')
    comId = InternshipInfor.query.filter_by(Id=internId).first().comId
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    if internship.internStatus == 2:
        student = Student.query.filter_by(stuId=stuId).first()
        comInfor = ComInfor.query.filter_by(comId=comId).first()
        summary = Summary.query.filter_by(internId=internId).first()
        summary_doc = storage_list(internId, 'summary_doc')
        attachment = storage_list(internId, 'attachment')
        if request.method == 'POST':
            print(request.form)
            for x in request.form:
                print(x)
                # 下载文件
                if 'download' in x:
                    return storage_download(internId)
                # 上传文件
                elif 'upload' in x:
                    # flag = storage_upload(internId, x)
                    flag = storage_upload(internId)
                    if flag:
                        flash('上传成功')
                    else:
                        flash('上传失败,请重试')
                # 重命名/删除
                elif 'action' in x:
                    action = request.form.get('action')
                    file_name = request.form.get('file_name')
                    dest_path = request.form.get('dest_path')
                    storage_path = os.path.join(storage_cwd(internId, dest_path), file_name)
                    pdf_path = os.path.join(pdf_cwd(internId, dest_path), pdf_postfix(file_name))
                    if action == 'delete':
                        os.remove(pdf_path)
                        os.remove(storage_path)
                        flash('删除成功！')
                    elif action == 'rename_begin':
                        rename = file_name
                        # 跳转到可编辑文件名的页面
                        return render_template('xSum_fileManager.html', Permission=Permission, comInfor=comInfor,
                                               internship=internship, student=student, summary=summary,
                                               attachment=attachment, summary_doc=summary_doc, rename=rename)
                    # 确认重命名
                    elif action == 'rename_comfirm':
                        new_name = request.form.get('new_name')
                        os.rename(pdf_path, os.path.join(pdf_cwd(internId, dest_path), pdf_postfix(new_name)))
                        os.rename(storage_path, os.path.join(storage_cwd(internId, dest_path), new_name))
                        flash('重命名成功！')
            return redirect(url_for('.xSum_fileManager', stuId=stuId, internId=internId))

        return render_template('xSum_fileManager.html', Permission=Permission, comInfor=comInfor, internship=internship,
                               student=student, summary=summary, attachment=attachment, summary_doc=summary_doc)


# 实习评分详情
@main.route('/xSumScore', methods=['GET', 'POST'])
@login_required
def xSumScore():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    internId = request.args.get('internId')
    comId = InternshipInfor.query.filter_by(Id=internId).first().comId
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    path = os.path.join(os.path.abspath('.'), 'app/static/storage', internId, 'score_img')
    sumScore = Summary.query.filter_by(internId=internId).first().sumScore
    if not sumScore:
        flash('请先完善实习成绩信息！')
        return redirect(url_for('.xSumScoreEdit', internId=internId, stuId=stuId))
    file_path = {}
    if os.path.exists(path):
        file = os.listdir(path + '/comscore')
        if file:
            file_path['comscore'] = path[path.find('/static'):] + '/comscore/' + file[0]
        file = os.listdir(path + '/schscore')
        if file:
            file_path['schscore'] = path[path.find('/static'):] + '/schscore/' + file[0]
    # download
    if request.method == 'POST':
        file_name = request.form.get('file_path')[request.form.get('file_path').find('score/') + 6:]
        return send_file(os.path.join(os.path.abspath('.'), 'app/') + request.form.get('file_path'), as_attachment=True,
                         attachment_filename=file_name.encode('utf-8'))
    if internship.internStatus == 2:
        student = Student.query.filter_by(stuId=stuId).first()
        comInfor = ComInfor.query.filter_by(comId=comId).first()
        summary = Summary.query.filter_by(internId=internId).first()
        return render_template('xSumScore.html', Permission=Permission, comInfor=comInfor, internship=internship,
                               student=student, summary=summary, file_path=file_path)


# 编辑实习分数
@main.route('/xSumScoreEdit', methods=['GET', 'POST'])
@login_required
def xSumScoreEdit():
    form = xSumScoreForm()
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    internId = request.args.get('internId')
    comId = InternshipInfor.query.filter_by(Id=internId).first().comId
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    path = storage_cwd(internId, 'score_img')
    file_path = {}
    if os.path.exists(path):
        file = os.listdir(path + '/comscore')
        if file:
            file_path['comscore'] = file[0]
        file = os.listdir(path + '/schscore')
        if file:
            file_path['schscore'] = file[0]
    if internship.internStatus == 2:
        student = Student.query.filter_by(stuId=stuId).first()
        comInfor = ComInfor.query.filter_by(comId=comId).first()
        summary = Summary.query.filter_by(internId=internId).first()
    if request.method == 'POST':
        if request.form.get('action') == 'upload':
            summary.comScore = form.comScore.data
            summary.schScore = form.schScore.data
            summary.sumScore = float(form.comScore.data) * 0.7 + float(form.schScore.data) * 0.3
            db.session.add(summary)
            paths = []
            paths.append(os.path.join(storage_cwd(internId, 'score_img'), 'comscore'))
            paths.append(paths[0].replace('comscore', 'schscore'))
            # mkdir
            for path in paths:
                if not os.path.exists(path):
                    os.makedirs(path)
            try:
                db.session.commit()
                if form.comfile.data:
                    form.comfile.data.save(paths[0] + '/' + form.comfile.data.filename)
                if form.schfile.data:
                    form.schfile.data.save(paths[1] + '/' + form.schfile.data.filename)
                flash('保存成功!!')
                return redirect(url_for('.xSumScore', internId=internId, stuId=stuId))
            except Exception as e:
                db.session.rollback()
                flash('保存失败!')
                print('xSumScoreEdit:', e)
                return redirect(url_for('.xSumScoreEdit', internId=internId, stuId=stuId))
        elif request.form.get('action').find('delete') != -1:
            path = os.path.join(path, request.form.get('filename'))
            os.remove(path)
            flash('删除成功')
            return redirect(url_for('.xSumScoreEdit', internId=internId, stuId=stuId))
    return render_template('xSumScoreEdit.html', Permission=Permission, form=form, student=student,
                           internship=internship, comInfor=comInfor, summary=summary, file_path=file_path)



# 审核通过总结成果
@main.route('/xSum_comfirm', methods=["POST", "GET"])
@not_student_login
def xSum_comfirm():
    if current_user.can(Permission.STU_SUM_SCO_CHECK):
        internId = request.form.get('internId')
        sumCheck = request.form.get('sumCheck')
        stuId = request.form.get('stuId')
        sumCheckOpinion = request.form.get('sumCheckOpinion')
        comId = InternshipInfor.query.filter_by(Id=internId).first().comId
        com = ComInfor.query.filter(comId == comId).first()
        checkTime = datetime.now().date()
        checkTeaId = current_user.get_id()
        try:
            if sumCheckOpinion:
                db.session.execute(
                    'update Summary set sumCheck=%s, sumCheckOpinion="%s", sumCheckTeaId=%s, sumCheckTime="%s" where internId=%s' % (
                        sumCheck, sumCheckOpinion, checkTeaId, checkTime, internId))
                # 作消息提示
                db.session.execute('update Student set internCheck=1 where stuId=%s' % stuId)
            else:
                db.session.execute(
                    'update Summary set sumCheck=%s, sumCheckTeaId=%s, sumCheckTime="%s" where internId=%s' % (
                        sumCheck, checkTeaId, checkTime, internId))
                # 作消息提示
                db.session.execute('update Student set sumCheck=1 where stuId=%s' % stuId)
            # 若所选企业或实习信息未被审核通过,且用户有审核权限,自动审核通过企业和实习信息
            comId = InternshipInfor.query.filter_by(Id=internId).first().comId
            com = ComInfor.query.filter_by(comId=comId).first()
            if com.comCheck != 2:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    db.session.execute('update ComInfor set comCheck=2 where comId=%s' % comId)
                    if current_user.can(Permission.STU_INTERN_CHECK):
                        db.session.execute(
                            'update InternshipInfor set internCheck=2, icheckTime="%s", icheckTeaId=%s where Id = %s' % (
                                checkTime, checkTeaId, internId))
                        # 作消息提示
                        db.session.execute('update Student set internCheck=1 where stuId=%s' % stuId)
        except Exception as e:
            db.session.rollback()
            print(datetime.now(), ":", current_user.get_id(), "审核实习总结失败", e)
            flash("审核实习总结失败")
            return redirect("/")
        flash("审核实习总结成功")
    return redirect(url_for('.xSum', stuId=stuId, internId=internId))


# 批量审核总结和成果
@main.route('/stuSum_allCheck', methods=['GET', 'POST'])
@not_student_login
@update_intern_internStatus
def stuSum_allCheck():
    if not current_user.can(Permission.STU_SUM_SCO_CHECK):
        flash("非法操作")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    # now = datetime.now().date()
    checkTime = datetime.now().date()
    checkTeaId = current_user.get_id()
    form = searchForm()
    grade = {}
    classes = {}
    major = {}
    intern = create_intern_filter(grade, major, classes, 2)
    pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
        .filter(InternshipInfor.internStatus == 2, InternshipInfor.internCheck == 2, Summary.sumCheck != 2) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName,
                     InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end,
                     InternshipInfor.internCheck, Summary.sumScore, Summary.sumCheck) \
        .paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定实习审核通过
    if request.method == "POST":
        try:
            internId = request.form.getlist('approve[]')
            for x in internId:
                db.session.execute(
                    'update Summary set sumCheck=1, sumCheckTeaId=%s, sumCheckTime="%s" where internId=%s' % (
                        CheckTeaId, CheckTime, x))
                # 作消息提示
                stuId = InternshipInfor.query.filter_by(Id=x).first().stuId
                db.session.execute('update Student set sumCheck=1 where stuId=%s' % stuId)
                # # 若所选企业或实习信息未被审核通过,且用户有审核权限,自动审核通过企业和实习信息
                # comId = InternshipInfor.query.filter_by(Id=x).first().comId
                # com = ComInfor.query.filter_by(comId=comId).first()
                # if com.comCheck != 2:
                #     if current_user.can(Permission.COM_INFOR_CHECK):
                #         db.session.execute('update ComInfor set comCheck=2 where comId=%s' % comId)
                #         if current_user.can(Permission.STU_INTERN_CHECK):
                #             db.session.execute('update InternshipInfor set internCheck=2 where Id = %s' % x)
                #             # 作消息提示
                #             stuId = InternshipInfor.query.filter(Id=x).first().stuId
                #             db.session.execute('update Student set sumCheck=1 where stuId=%s' % stuId)
        except Exception as e:
            db.session.rollback()
            print(datetime.now(), ":", current_user.get_id(), "审核实习总结失败", e)
            flash("审核实习总结失败")
            return redirect("/")
        flash('审核实习总结成功')
        return redirect(url_for('.stuSum_allCheck', page=pagination.page))
    return render_template('stuSum_allCheck.html', Permission=Permission, internlist=internlist,
                           pagination=pagination, major=major, classes=classes, grade=grade, form=form)


# 批量删除总结和成果
@main.route('/stuSum_allDelete', methods=['GET', 'POST'])
@not_student_login
def stuSum_allDelete():
    if not current_user.can(Permission.STU_SUM_SCO_CHECK):
        flash("非法操作")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    form = searchForm()
    grade = {}
    classes = {}
    major = {}
    intern = create_intern_filter(grade, major, classes, 2)
    now = datetime.now().date()
    pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
        .filter(InternshipInfor.internCheck ==2 ) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, InternshipInfor.comId,
                     InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck, InternshipInfor.address, InternshipInfor.task,
                     InternshipInfor.opinion, InternshipInfor.icheckTime, Summary.sumScore, Summary.sumCheck) \
        .order_by(Summary.sumCheck, InternshipInfor.end.desc()).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定删除实习
    if request.method == "POST":
        # 还需有[实习,日志] 删除权限
        if True:
            internId = request.form.getlist('approve[]')
            for x in internId:
                # 企业指导老师,日志,实习一同删除
                temp_intern = InternshipInfor.query.filter_by(Id=x).first()
                temp_comId = temp_intern.comId
                temp_stuId = temp_intern.stuId
                db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s' % (temp_stuId, temp_comId))
                db.session.execute('delete from Summary where internId=%s' % x)
                db.session.execute('delete from Journal where internId=%s' % x)
                db.session.execute('delete from InternshipInfor where Id=%s' % x)
                # 企业累计实习人数减一
                db.session.execute('update ComInfor set students = students -1 where comId=%s' % temp_comId)
            flash('删除成功')
            return redirect(url_for('.stuSum_allDelete', page=pagination.page))
    return render_template('stuSum_allDelete.html', Permission=Permission, internlist=internlist,
                               pagination=pagination, grade=grade, classes=classes, major=major, form=form)


# 下拉框管理
@main.route('/selectManage',methods=['GET','POST'])
@login_required
@update_grade_major_classes
def selectManage():
    if not current_user.can(Permission.SELECT_MANAGE):
        flash('非法操作！')
        return redirect('/')
    majors=Major.query.order_by(Major.major).all()
    grades=Grade.query.order_by(Grade.grade).all()
    classess=Classes.query.order_by(Classes.classes).all()
    major=request.args.get('major')
    classes=request.args.get('classes')
    grade=request.args.get('grade')
    try:
        if major:
            db.session.execute("delete from Major where major='%s'"%major)
            flash('删除专业成功！')
            return redirect(url_for('.selectManage'))
        if classes:
            db.session.execute('delete from Classes where classes=%s'%classes)
            flash('删除班级成功！')
            return redirect(url_for('.selectManage'))
        if grade:
            db.session.execute('delete from Grade where grade=%s'%grade)
            flash('删除年级成功！')            
            return redirect(url_for('.selectManage'))
    except Exception as e:
        flash('删除失败,请重试')
        print('删除年级，专业，班级：',e)
        db.session.rollback()
        return redirect(url_for('.selectManage'))
    if request.method=='POST':
        for x in request.form:
            try:
                if x=='major':
                    major=Major(major=request.form.get('major'))
                    db.session.add(major)
                    db.session.commit()
                    flash('添加专业成功！')
                    return redirect(url_for('.selectManage'))
                elif x=='grade':
                    grade=Grade(grade=request.form.get('grade'))
                    db.session.add(grade)
                    db.session.commit()
                    flash('添加年级成功！')
                    return redirect(url_for('.selectManage'))
                elif x=='classes':
                    classes=Classes(classes=request.form.get('classes'))
                    db.session.add(classes)
                    db.session.commit()
                    flash('添加班级成功！')
                    return redirect(url_for('.selectManage'))
            except Exception as e:
                flash('添加失败，请重试！')
                return redirect(url_for('.selectManage'))
    return render_template('selectManage.html',Permission=Permission,majors=majors,grades=grades,classess=classess)

#上传探访记录
@main.route('/upload_Visit',methods=['GET','POST'])
@login_required
def upload_Visit():
    path=None
    files=[]
    filename=request.args.get('filename')
    userId=None
    url='%s/visit/%s'%(STORAGE_FOLDER,current_user.teaId)
    if os.path.exists(url):
        files=os.listdir(url)
        userId=current_user.teaId
    if filename:
        path=os.path.join(STATIC_STORAGE,'visit',userId,filename)
    if request.method=='POST':
        try:
            if 'delete' in request.form:
                os.remove(os.path.join(STORAGE_FOLDER,'visit',userId,request.form.get('delete')))
                flash('删除成功！')
                return redirect(url_for('.upload_Visit'))
            if 'download' in request.form:
                file_name=request.form.get('download')
                return send_file(os.path.join(STORAGE_FOLDER,'visit',userId,file_name), as_attachment=True,
                             attachment_filename=file_name.encode('utf-8'))
            file=request.files.get('.upload_Visit')
            if file:
                if not os.path.exists('%s/visit/%s'%(STORAGE_FOLDER,userId)):
                    os.system('mkdir %s/visit/%s' % (STORAGE_FOLDER,userId))
                file.save('%s/visit/%s/%s'%(STORAGE_FOLDER,userId,file.filename))
                flash('上传成功！')
                return redirect(url_for('.selectStudent',filename=file.filename))
        except Exception as e:
            flash('操作失败，请重试！')
            print('探访记录：',e)
            return redirect(url_for('.upload_Visit'))
    return render_template('visit.html',Permission=Permission,path=path,files=files)

#选择探访学生
@main.route('/selectStudent',methods=['GET','POST'])
@login_required
def selectStudent():
    grade={}
    major={}
    classes={}
    page = request.args.get('page', 1, type=int)
    pagination=create_stu_filter(grade, major, classes).join(InternshipInfor,InternshipInfor.stuId==Student.stuId).join(ComInfor,ComInfor.comId==InternshipInfor.comId)\
    .add_columns(ComInfor.comName,Student.stuName,InternshipInfor.Id,Student.stuId,InternshipInfor.start,InternshipInfor.end).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    form=searchForm()
    userId=None
    userId=current_user.teaId
    if request.method=='POST':
        filename=request.args.get('filename')
        for x in request.form.getlist('approve[]'):
            source='%s/visit/%s/%s'%(STORAGE_FOLDER,userId,filename)
            direction='%s/%s/visit'%(STORAGE_FOLDER,x)
            if not os.path.exists(direction):
                os.mkdir(direction)
            shutil.copyfile(source,os.path.join(direction,filename))
        flash('操作成功！')
        return redirect(url_for('.visit'))
    return render_template('selectStudent.html',Permission=Permission,form=form,internlist=internlist,grade=grade,classes=classes,major=major,pagination=pagination)

#学生的被探访记录
@main.route('/visit',methods=['GET','POST'])
@login_required
def visit():
    internId=request.args.get('internId')
    url='%s/%s/visit'%(STORAGE_FOLDER,internId)
    file=None
    print(url)
    if os.path.exists(url):
        file=os.listdir(url)
    path=None
    filename=request.args.get('filename')
    if filename:
        path='%s/%s/visit/%s'%(STATIC_STORAGE,internId,filename)
    if request.method=='POST':
        try:
            if 'delete' in request.form:
                os.remove(os.path.join(url,request.form.get('delete')))
                flash('删除成功！')
                return redirect(url_for('.visit',internId=internId))
            if 'download' in request.form:
                file_name=request.form.get('download')
                return send_file(os.path.join(url,file_name), as_attachment=True,
                             attachment_filename=file_name.encode('utf-8'))
            flash('操作成功！')
            return redirect(url_for('.visit',internId=internId))
        except Exception as e:
            flash('操作失败！请重试！')
            return redirect(url_for('.visit',internId=internId))
    return render_template('visit.html',Permission=Permission,path=path,file=file,internId=internId)
