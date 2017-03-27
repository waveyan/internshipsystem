# -*- coding: utf-8 -*-

from flask import render_template, url_for, flash, redirect, request, session, send_file
from .form import searchForm, comForm, internshipForm, journalForm, stuForm, teaForm, permissionForm, schdirteaForm, \
    comdirteaForm, xSumScoreForm,visitForm,introduceForm
from . import main
from ..models import Permission, InternshipInfor, ComInfor, SchDirTea, ComDirTea, Student, Journal, Role, Teacher, \
    not_student_login, update_intern_internStatus, update_intern_jourCheck, Summary,Major,Grade,Classes,update_grade_major_classes,\
    Visit,Visit_Intern,Introduce
from flask.ext.login import current_user, login_required
from .. import db
from sqlalchemy import func, desc, and_, distinct
from datetime import datetime, timedelta, date
import xlwt, xlrd, os, random, subprocess, re,shutil
from collections import OrderedDict
from werkzeug.utils import secure_filename
from sqlalchemy.orm import aliased
from ..auth.views import logout_url
from ..email import send_email
import time
import json



# -----------------------------统计----------------------------------------
#地域统计筛选
def update_area_filter():
    major=request.args.get('major')
    grade=request.args.get('grade')
    m=request.args.get('m')
    g=request.args.get('g')
    if m:
        session['major']=None
    if g:
        session['grade']=None
    #为了在统计页面上与major数据类型一致
    if grade:
        grade=int(grade)
    if major:
        session['major']=major
    elif grade:
        session['grade']=grade
    elif not m and not g:
        session['major']=None
        session['grade']=None
    if session['major']:
        sql="select comCity,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId and major='%s' group by comCity order by count(i.comId) desc"%session['major']
        # cominfor=db.session.query(ComInfor.comAddress,func.sum(InternshipInfor.comId)).outerjoin(InternshipInfor,InternshipInfor.comId==ComInfor.comId)\
        # .outerjoin(Student,Student.stuId==InternshipInfor.stuId).group_by(ComInfor.comAddress).order_by(func.sum(ComInfor.comId).desc()).filter(Student.major==session['major'])
        if session['grade']:
            sql="select comCity,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId and major='%s' and grade=%s group by comCity order by count(i.comId) desc"%(session['major'],session['grade'])
            # cominfor=cominfor.filter(Student.grade==session['grade'])

    if session['grade']:
        sql="select comCity,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId and grade='%s' group by comCity order by count(i.comId) desc"%session['grade']
        # cominfor=db.session.query(ComInfor.comAddress,func.sum(ComInfor.students)).outerjoin(InternshipInfor,InternshipInfor.comId==ComInfor.comId)\
        # .outerjoin(Student,Student.stuId==InternshipInfor.stuId).group_by(ComInfor.comAddress).order_by(func.sum(ComInfor.students).desc()).filter(Student.grade==session['grade'])
        if session['major']:
            sql="select comCity,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId and major='%s' and grade=%s group by comCity order by count(i.comId) desc"%(session['major'],session['grade'])
            # cominfor=cominfor.filter(Student.major==session['major'])

    if not session['major'] and not session['grade']:
        sql='select comCity,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId group by comCity order by count(i.comId) desc'
        # cominfor=db.session.query(ComInfor.comAddress,func.sum(ComInfor.students)).outerjoin(InternshipInfor,InternshipInfor.comId==ComInfor.comId)\
        # .outerjoin(Student,Student.stuId==InternshipInfor.stuId).group_by(ComInfor.comAddress).order_by(func.sum(ComInfor.students).desc())
    return sql

#企业统计筛选
def update_company_filter():
    major=request.args.get('major')
    grade=request.args.get('grade')
    m=request.args.get('m')
    g=request.args.get('g')
    if m:
        session['major']=None
    if g:
        session['grade']=None
    #为了在统计页面上与major数据类型一致
    if grade:
        grade=int(grade)
    if major:
        session['major']=major
    elif grade:
        session['grade']=grade
    elif not m and not g:
        session['major']=None
        session['grade']=None
    if session['major']:
        sql="select comName,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId and major='%s' group by i.comId,comName order by count(i.comId) desc"%session['major']
        if session['grade']:
            sql="select comName,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId and major='%s' and grade=%s group by i.comId,comName order by count(i.comId) desc"%(session['major'],session['grade'])
    if session['grade']:
        sql="select comName,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId and grade='%s' group by i.comId,comName order by count(i.comId) desc"%session['grade']
        if session['major']:
            sql="select comName,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId and major='%s' and grade=%s group by i.comId,comName  order by count(i.comId) desc"%(session['major'],session['grade'])
    if not session['major'] and not session['grade']:
        sql='select comName,count(i.comId) from ComInfor as c ,InternshipInfor as i,Student as s where c.comId=i.comId and s.stuId=i.stuId group by i.comId,comName order by count(i.comId) desc'
    return sql


# 统计--地域统计图
@main.route('/statistics_area_visual', methods=['GET', 'POST'])
def statistics_area_visual():
    comlist = []
    index = 0
    major=Major.query.all()
    grade=Grade.query.all()
    sql=update_area_filter()
    cominfor=db.session.execute(sql)
    #初始化，防止数据不够时抛错
    for i in range(7):
        comlist.append(None)
    for com in cominfor:
        if index < 6:
            # com[1] 为学生人数
            comlist[index]={'comCity': com[0], 'students': com[1]}
            index = index + 1
        #    if index == 6:
        #        comlist[index]={'comCity': '其他', 'students': 0}
        # else:
        #    comlist[6]['students'] = comlist[6]['students'] + com[1]
    return render_template('statistics_area_visual.html', Permission=Permission, comlist=comlist,major=major,grade=grade)


# 统计--企业统计图
@main.route('/statistics_com_visual', methods=['GET', 'POST'])
@login_required
def statistics_com_visual():
    comlist = []
    index = 0
    major=Major.query.all()
    grade=Grade.query.all()
    sql=update_company_filter()
    cominfor=db.session.execute(sql)
    #初始化，防止数据不够时抛错
    for i in range(7):
        comlist.append(None)
    for com in cominfor:
        if index < 6:
            comlist[index]={'comName': com[0], 'students': com[1]}
            index = index + 1
    return render_template('statistics_com_visual.html', Permission=Permission, comlist=comlist,grade=grade,major=major)


# 统计--企业排行
@main.route('/statistics_com_rank', methods=['GET', 'POST'])
@login_required
def statistics_com_rank():

    comlist = []
    index = 0
    major = Major.query.all()
    grade = Grade.query.all()
    sql = update_company_filter()
    cominfor = db.session.execute(sql)
    form = searchForm()
    page = request.args.get('page', 1, type=int)
   # cominfor =
    #pagination = ComInfor.query.filter(ComInfor.students != 0).order_by(ComInfor.students.desc()).paginate(page,
                                                                                                        #   per_page=8,
                                                                                                          #error_out=False)
    #pagination = ComInfor.query.filter(ComInfor.students != 0).filter_by(ComInfro.students==grade)
    #pagination = ComInfor.query.filter(ComInfor.students != 0).join(InternshipInfor, ComInfor.comId==InternshipInfor.comId).join(Student, Student.stuId==InternshipInfor.stuId)\
     #   .add_columns(Student.grade, ComInfor.comId, ComInfor.comId, ComInfor.comName, ComInfor.comUrl,
     #                ComInfor.comPhone, ComInfor.students, Student.stuId).order_by(ComInfor.students.desc())\
    #    .paginate(page, per_page=8, error_out=False)
    if session['grade']:
        pagination = ComInfor.query.filter(ComInfor.students != 0).join(InternshipInfor,
                                                                    ComInfor.comId == InternshipInfor.comId).join(
        Student, Student.stuId == InternshipInfor.stuId).with_entities(
        func.count(InternshipInfor.Id).label('sum_students'), Student.grade, ComInfor.comId, ComInfor.comId,
        ComInfor.comName, ComInfor.comUrl, ComInfor.comPhone, ComInfor.students, Student.stuId).order_by(
        desc('sum_students')).group_by(ComInfor.comId).filter(Student.grade == session['grade']).paginate(1,per_page=20,error_out=False)
        if session['major']:
            pagination = ComInfor.query.filter(ComInfor.students != 0).join(InternshipInfor,
                                                                            ComInfor.comId == InternshipInfor.comId).join(
                Student, Student.stuId == InternshipInfor.stuId).with_entities(
                func.count(InternshipInfor.Id).label('sum_students'), Student.grade, ComInfor.comId, ComInfor.comId,
                ComInfor.comName, ComInfor.comUrl, ComInfor.comPhone, ComInfor.students, Student.stuId).order_by(
                desc('sum_students')).group_by(ComInfor.comId).filter(Student.grade == session['grade']).filter(Student.major == session['major']).paginate(1,
                                                                                                                  per_page=20,
                                                                                                              error_out=False)
    if session['major']:
        pagination = ComInfor.query.filter(ComInfor.students != 0).join(InternshipInfor,
                                                                        ComInfor.comId == InternshipInfor.comId).join(
            Student, Student.stuId == InternshipInfor.stuId).with_entities(
            func.count(InternshipInfor.Id).label('sum_students'), Student.grade, ComInfor.comId, ComInfor.comId,
            ComInfor.comName, ComInfor.comUrl, ComInfor.comPhone, ComInfor.students, Student.stuId).order_by(
            desc('sum_students')).group_by(ComInfor.comId).filter(Student.major == session['major']).paginate(1,
                                                        per_page=20,
                                                        error_out=False)
        if session['grade']:
            pagination = ComInfor.query.filter(ComInfor.students != 0).join(InternshipInfor,
                                                                            ComInfor.comId == InternshipInfor.comId).join(
                Student, Student.stuId == InternshipInfor.stuId).with_entities(
                func.count(InternshipInfor.Id).label('sum_students'), Student.grade, ComInfor.comId, ComInfor.comId,
                ComInfor.comName, ComInfor.comUrl, ComInfor.comPhone, ComInfor.students, Student.stuId).order_by(
                desc('sum_students')).group_by(ComInfor.comId).filter(Student.grade == session['grade']).filter(
                Student.major == session['major']).paginate(1,
                                                            per_page=20,
                                                            error_out=False)

    if not session['major'] and not session['grade']:
        pagination = ComInfor.query.filter(ComInfor.students != 0).order_by(ComInfor.students.desc()).paginate(page,
                    per_page=20,
                        error_out=False)

    comInfor = pagination.items
    return render_template('statistics_com_rank.html', form=form, Permission=Permission, pagination=pagination,
                           comInfor=comInfor, grade=grade, major=major)

# 统计--地域排行
@main.route('/statistics_area_rank', methods=['GET', 'POST'])
@login_required
def statistics_area_rank():
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.outerjoin(ComInfor, InternshipInfor.comId==ComInfor.comId).with_entities(ComInfor.comCity, func.count(InternshipInfor.Id).label('sum_students')).order_by(desc('sum_students')).group_by(ComInfor.comCity).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    return render_template('statistics_area_rank.html', form=form, Permission=Permission, pagination=pagination,
                           comInfor=comInfor)


# --------------------------------------------------------------------
# 首页
@main.route('/', methods=['GET', 'POST'])
def index():
    if get_export_all_update_status() is 'empty':
        get_export_all_generate()
    if request.args.get("isLogout"):
        return redirect(logout_url)
    content_html=db.session.execute('select content_html from Introduce where Id=(select max(Id) from Introduce)')
    return render_template('index.html', Permission=Permission,content_html=content_html)


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
                db.session.rollback()
                flash('error!!!')
                return redirect('/')
        stuId = current_user.stuId
        student = Student.query.filter_by(stuId=stuId).first()
        internship = InternshipInfor.query.filter_by(stuId=stuId).all()
        # 让添加实习企业 addcominfor 下一步跳转到 addinternship
        if len(internship)==0:
            flash('您还没完成实习信息的填写，请完善相关实习信息！')
            return redirect(url_for('.addcominfor', from_url='stuInternList'))
        else:
            pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Summary,Summary.internId==InternshipInfor.Id) \
                .add_columns(Summary.sumScore,ComInfor.comName, ComInfor.comCity,InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start,
                             InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.time) \
                .filter(InternshipInfor.stuId == stuId).order_by(
                func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8, error_out=False)
            internlist = pagination.items
            #指导老师
            schdirtea=list()
            comdirtea=list()
            for i in internlist:
                comdirtea.append(ComDirTea.query.filter_by(stuId=stuId,comId=i.comId).all())
                schdirtea.append(db.session.execute('select teaName from SchDirTea,Teacher where SchDirTea.teaId=Teacher.teaId and internId=%s'%i.Id))
            internlist=zip(internlist,comdirtea,schdirtea)
            return render_template('stuInternList.html', internlist=internlist, Permission=Permission,
                                   student=student, pagination=pagination, form=form,
                                   grade=grade, major=major, classes=classes)
    elif current_user.can(Permission.STU_INTERN_LIST):
        # 函数返回的intern已经join了Student
        intern = create_intern_filter(grade, major, classes, 0)
        intern_org = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Summary,Summary.internId==InternshipInfor.Id).outerjoin(
            Teacher, Teacher.teaId == InternshipInfor.icheckTeaId)\
            .add_columns(Summary.sumScore,InternshipInfor.stuId, Student.stuName, ComInfor.comName, ComInfor.comId, ComInfor.comCity,
                         InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                         InternshipInfor.internCheck, InternshipInfor.task, InternshipInfor.post, Teacher.teaName,
                         InternshipInfor.opinion, InternshipInfor.icheckTime, InternshipInfor.time) \
            .order_by(func.field(InternshipInfor.internStatus, 1, 0, 2))
        pagination = intern_org.paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        #指导老师
        schdirtea=list()
        comdirtea=list()
        for internship in internlist:
            comdirtea.append(ComDirTea.query.filter_by(stuId=internship.stuId,comId=internship.comId).all())
            schdirtea.append(db.session.execute('select teaName from SchDirTea,Teacher where SchDirTea.teaId=Teacher.teaId and internId=%s'%internship.Id))
        internlist=zip(internlist,comdirtea,schdirtea)
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
    pagination = ComInfor.query.order_by(ComInfor.comDate.desc()).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items

    return render_template('selectCom.html', form=form, Permission=Permission, comInfor=comInfor, pagination=pagination)


CITY_LIST = ['北京', '上海', '天津', '重庆', '香港', '澳门', '石家庄', '沧州', '承德', '秦皇岛', '唐山', '保定', '廊坊', '邢台', '衡水', '张家口', '邯郸', '任丘', '河间', '泊头', '武安', '沙河', '南宫', '深州', '冀州', '黄骅', '高碑店', '安国', '涿州', '定州', '三河', '霸州', '迁安', '遵化', '鹿泉', '新乐', '晋州', '藁城', '辛集', '太原', '长治', '大同', '阳泉', '朔州', '临汾', '晋城', '忻州', '运城', '晋中', '吕梁', '古交', '潞城', '高平', '原平', '孝义', '汾阳', '介休', '侯马', '霍州', '永济', '河津', '沈阳', '大连', '本溪', '阜新', '葫芦岛', '盘锦', '铁岭', '丹东', '锦州', '营口', '鞍山', '辽阳', '抚顺', '朝阳', '瓦房店', '兴城', '新民', '普兰店', '庄河', '北票', '凌源', '调兵山', '开原', '灯塔', '海城', '凤城', '东港', '大石桥', '盖州', '凌海', '北镇', '长春', '白城', '白山', '吉林', '辽源', '四平', '通化', '松原', '延吉', '珲春', '龙井', '舒兰', '临江', '公主岭', '梅河口', '德惠', '九台', '榆树', '磐石', '蛟河', '桦甸', '洮南', '大安', '双辽', '集安', '图们', '敦化', '和龙', '哈尔滨', '大庆', '大兴安岭', '鹤岗', '黑河', '鸡西', '佳木斯', '牡丹江', '七台河', '双鸭山', '齐齐哈尔', '伊春', '绥化', '虎林', '五常', '密山', '宁安', '漠河', '海伦', '肇东', '安达', '海林', '绥芬河', '富锦', '同江', '铁力', '五大连池', '北安', '讷河', '阿城', '尚志', '双城', '南京', '苏州', '扬州', '无锡', '南通', '常州', '连云港', '徐州', '镇江', '淮安', '宿迁', '泰州', '太仓', '盐城', '高邮', '新沂', '金坛', '溧阳', '淮阴', '江宁', '睢宁', '清江', '昆山', '常熟', '江阴', '宜兴', '邳州', '张家港', '吴江', '如皋', '海门', '启东', '大丰', '东台', '仪征', '扬中', '句容', '丹阳', '兴化', '姜堰', '泰兴', '靖江', '杭州', '宁波', '温州', '丽水', '奉化', '宁海', '临海', '三门', '绍兴', '舟山', '义乌', '北仑', '慈溪', '象山', '余姚', '天台', '温岭', '仙居', '台州', '嘉兴', '湖州', '衢州', '金华', '余杭', '德清', '海宁', '临安', '富阳', '建德', '平湖', '桐乡', '诸暨', '上虞', '嵊州', '江山', '兰溪', '永康', '东阳', '瑞安', '乐清', '龙泉', '合肥', '黄山', '芜湖', '铜陵', '安庆', '滁州', '宣城', '阜阳', '淮北', '蚌埠', '池州', '青阳', '九华山景区', '黄山景区', '巢湖', '亳州', '马鞍山', '宿州', '六安', '淮南', '绩溪', '界首', '明光', '天长', '桐城', '宁国', '福州', '厦门', '泉州', '漳州', '龙岩', '三明', '南平', '永安', '宁德', '莆田', '闽侯', '福鼎', '罗源', '仙游', '福清', '长乐', '云霄', '长泰', '东山岛', '邵武', '石狮', '晋江', '建阳', '福安', '漳平', '龙海', '南安', '建瓯', '武夷山', '南昌', '九江', '赣州', '景德镇', '萍乡', '新余', '吉安', '宜春', '抚州', '上饶', '鹰潭', '陵川', '瑞金', '井冈山', '瑞昌', '乐平', '南康', '德兴', '丰城', '樟树', '高安', '贵溪', '济南', '青岛', '烟台', '威海', '潍坊', '德州', '滨州', '东营', '聊城', '菏泽', '济宁', '临沂', '淄博', '泰安', '枣庄', '日照', '莱芜', '海阳', '平度', '莱阳', '青州', '肥城', '章丘', '即墨', '利津', '武城', '桓台', '沂源', '曲阜', '龙口', '胶州', '胶南', '莱西', '临清', '乐陵', '禹城', '安丘', '昌邑', '高密', '诸城', '寿光', '栖霞', '莱州', '蓬莱', '招远', '文登', '荣成', '乳山', '滕州', '兖州', '邹城', '新泰', '郑州', '安阳', '济源', '鹤壁', '焦作', '开封', '濮阳', '三门峡', '驻马店', '商丘', '新乡', '信阳', '许昌', '周口', '南阳', '洛阳', '平顶山', '漯河', '中牟', '洛宁', '荥阳', '登封', '项城', '灵宝', '义马', '舞钢', '长葛', '禹州', '林州', '辉县', '卫辉', '沁阳', '孟州', '偃师', '新密', '登封', '新郑', '汝州', '永城', '邓州', '巩义', '武汉', '十堰', '宜昌', '鄂州', '黄石', '襄樊', '荆州', '荆门', '孝感', '黄冈', '咸宁', '随州', '恩施', '仙桃', '天门', '潜江', '神农架', '沙市', '老河口', '利川', '当阳', '枝江', '宜都', '松滋', '洪湖', '石首', '赤壁', '大冶', '麻城', '武穴', '广水', '安陆', '应城', '汉川', '钟祥', '宜城', '枣阳', '丹江口', '长沙', '张家界', '株洲', '韶山', '衡阳', '郴州', '冷水江', '娄底', '耒阳', '永州', '湘乡', '湘潭', '常德', '益阳', '怀化', '邵阳', '岳阳', '吉首', '大庸', '韶山', '常宁', '浏阳', '津市', '沅江', '汨罗', '临湘', '醴陵', '资兴', '武冈', '洪江', '广州', '深圳', '珠海', '东莞', '佛山', '潮州', '汕头', '湛江', '中山', '惠州', '河源', '揭阳', '梅州', '肇庆', '茂名', '云浮', '阳江', '江门', '韶关', '乐昌', '化州', '从化', '鹤山', '汕尾', '清远', '顺德', '雷州', '廉江', '吴川', '高州', '信宜', '阳春', '罗定', '四会', '高要', '开平', '台山', '恩平', '陆丰', '普宁', '兴宁', '南雄', '连州', '英德', '增城', '南宁', '柳州', '北海', '百色', '梧州', '贺州', '玉林', '河池', '桂林', '钦州', '防城港', '来宾', '崇左', '贵港', '北流', '宜州', '桂平', '岑溪', '东兴', '凭祥', '合山', '海口', '三亚', '琼海', '儋州', '文昌', '万宁', '东方', '五指山', '成都', '内江', '峨眉山', '绵阳', '宜宾', '泸州', '攀枝花', '自贡', '资阳', '崇州', '西昌', '都江堰', '遂宁', '乐山', '达州', '江油', '大邑', '金堂', '德阳', '南充', '广安', '广元', '巴中', '雅安', '眉山', '马尔康', '康定', '三台', '丹棱', '梁平', '万县', '广汉', '汶川县', '什邡', '彭州', '绵竹', '邛崃', '阆中', '华蓥', '万源', '简阳', '贵阳', '安顺', '铜仁', '六盘水', '遵义', '毕节', '兴义', '凯里', '都匀', '福泉', '仁怀', '赤水', '清镇', '昆明', '西双版纳', '大理', '潞西', '思茅', '玉溪', '曲靖', '保山', '昭通', '临沧', '丽江', '文山', '个旧', '楚雄', '香格里拉', '宜良', '沅江', '安宁', '宣威', '瑞丽', '开远', '景洪', '拉萨', '那曲', '昌都', '山南', '日喀则', '噶尔', '林芝', '西安', '宝鸡', '延安', '兴平', '咸阳', '铜川', '渭南', '汉中', '榆林', '安康', '商洛', '周至', '韩城', '华阴', '兰州', '嘉峪关', '酒泉', '临夏', '白银', '天水', '武威', '张掖', '平凉', '庆阳', '定西', '成县', '合作', '敦煌', '金昌', '玉门', '西宁', '平安', '海晏', '同仁', '共和', '玛沁', '德令哈', '玉树', '格尔木', '呼和浩特', '海拉尔', '包头', '赤峰', '鄂尔多斯', '临河', '阿拉善左旗', '乌兰浩特', '通辽', '乌海', '集宁', '锡林浩特', '满洲里', '扎兰屯', '牙克石', '根河', '额尔古纳', '阿尔山', '霍林郭勒', '二连浩特', '丰镇', '银川', '石嘴山', '吴忠', '固原', '中卫', '灵武', '青铜峡', '乌鲁木齐', '克拉玛依', '哈密', '喀什', '吐鲁番', '石河子', '图木舒克', '和田', '昌吉', '阿图什', '库尔勒', '博乐', '伊宁', '阿拉尔', '阿克苏', '五家渠', '北屯', '阜康', '米泉', '奎屯', '塔城', '乌苏', '阿勒泰', '台北', '台中', '台南', '高雄', '基隆', '新竹', '嘉义', '宜兰', '桃园', '彰化', '苗栗', '云林', '屏东', '彭湖', '花莲']

def secure_comName(comName):
    comName = comName.replace(" ","")
    comName = comName.replace(",","")
    comName = comName.replace(".","")
    comName = comName.replace("(","")
    comName = comName.replace(")","")
    return comName

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
            # 在资料导出时, comName作为文件名, 所以需要检查
            comName = secure_comName(form.comName.data)
            comBrief = form.comBrief.data
            comAddress = form.comAddress.data
            comUrl = form.comUrl.data
            comMon = form.comMon.data
            comContact = form.comContact.data
            comProject = form.comProject.data
            comStaff = form.comStaff.data
            comPhone = form.comPhone.data
            comEmail = form.comEmail.data
            comFax = form.comFax.data
            comCity = form.comCity.data
            if comCity not in CITY_LIST:
                flash('请选择正确的城市')
                return redirect(url_for('.addcominfor'))
            # 通过企业名称, 城市, 地址来判断是否属于同一个公司
            is_exist = ComInfor.query.filter_by(comName=comName, comAddress=comAddress, comCity=comCity).all()
            if is_exist:
                flash('企业已存在')
                return redirect(url_for('.interncompany'))
            # 如果有企业信息审核权限的用户添加企业信息自动通过审核
            if current_user.can(Permission.COM_INFOR_CHECK):
                comInfor = ComInfor(
                    comName = comName,
                    comBrief = comBrief,
                    comAddress = comAddress,
                    comUrl = comUrl,
                    comMon = comMon,
                    comContact = comContact,
                    comProject = comProject,
                    comStaff = comStaff,
                    comPhone = comPhone,
                    comEmail = comEmail,
                    comCity = comCity,
                    comFax = comFax,
                    comCheck = 2)
            else:
                comInfor = ComInfor(
                    comName = comName,
                    comBrief = comBrief,
                    comAddress = comAddress,
                    comUrl = comUrl,
                    comMon = comMon,
                    comContact = comContact,
                    comProject = comProject,
                    comStaff = comStaff,
                    comPhone = comPhone,
                    comEmail = comEmail,
                    comCity = comCity,
                    comFax = comFax)

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
    #校内指导老师提示列表
    teachers=Teacher.query.all()
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
                if end > now:
                    internStatus = 1  # 实习中
            elif start > now:
                internStatus = 0  # 待实习
            else:
                internStatus = 1  # start=now, 实习中
            internship = InternshipInfor(
                task=request.form.get('task'),
		post=request.form.get('post'),
                start=start,
                end=end,
                time=datetime.now().date(),
                comId=comId,
                stuId=stuId,
                internStatus=internStatus
            )
            db.session.add(internship)
            #校外指导老师
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
            #校内指导老师
            while True:
                i = i + 1
                teaValue = request.form.get('teaName%s' % i)
                if teaValue:
                    tea=Teacher.query.filter_by(teaName=teaValue).first()
                    if tea:
                        internship.schdirtea.append(tea)
                    else:
                        tea=Teacher.query.filter_by(teaName='无该用户').first()
                        internship.schdirtea.append(tea)
                else:
                    break
            db.session.commit()
            # 初始化日志和总结成果
            internId = int(InternshipInfor.query.order_by(desc(InternshipInfor.Id)).first().Id)
            journal_init(internId)
            summary_init(internId)
            # 若所选企业未被审核通过,且用户有审核权限,自动审核通过企业
            if current_user.can(Permission.COM_INFOR_CHECK):
                try:
                    db.session.execute('update ComInfor set comCheck=2 where comId=%s' % comId)
                except Exception as e:
                    db.session.rollback()
                    print(datetime.now(), '/addinternship 审核企业失败:', e)
                    flash('所选企业审核失败,请重试')
                    return redirect('/')
            # 更新累计实习人数
            cominfor = ComInfor.query.filter_by(comId=comId).first()
            if cominfor.students:
                db.session.execute('update ComInfor set students=students+1 where comId=%s'%comId)
            else:
                db.session.execute('update ComInfor set students=1 where comId=%s'%comId)
            #上传协议书
            if request.files.getlist('image'):
                for i in request.files.getlist('image'):
                    i.save('%s/%s/agreement/%s' % (STORAGE_FOLDER, internId,i.filename))

            db.session.commit()
            flash('提交实习信息成功！')
            return redirect(url_for('.update_intern_filter',flag=5))
    except Exception as e:
        print("实习信息：", e)
        db.session.rollback()
        flash('提交实习信息失败，请重试！')
        return redirect(url_for('.addcominfor'))
    return render_template('addinternship.html', iform=iform, schdirteaform=schdirteaform, comdirteaform=comdirteaform,
                           Permission=Permission,teachers=teachers)


# 普通老师对于自己的指导学生, 带有'审核老师'的权限
def is_schdirtea(stuId):
    # if hasattr(current_user, 'teaId'):
    #     teaId = current_user.teaId
    #     flag = hasattr(SchDirTea.query.filter_by(stuId=stuId, teaId=teaId).first(), 'Id')
    #     return flag
    #当过该学生的校内指导老师都能审核该学生的所有实习信息
    flag=False
    all_internship=InternshipInfor.query.filter_by(stuId=stuId).all()
    for internship in all_internship:
        for tea in internship.schdirtea:
            if tea.teaId==current_user.get_id():
                flag=True
                break
    return flag


# 学生个人实习信息
@main.route('/xIntern', methods=['GET', 'POST'])
@login_required
def xIntern():
    internId = request.args.get('internId')
    if current_user.roleId == 0:
        stuId = current_user.stuId
        if stuId!=InternshipInfor.query.filter_by(Id=internId).first().stuId:
            flash('非法操作！')
            return redirect('/')
    else:
        stuId = request.args.get('stuId')
    comId = InternshipInfor.query.filter_by(Id=internId).first().comId
    student = Student.query.filter_by(stuId=stuId).first()
    #找到internship
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    #与本次internship相关的Teacher信息，包含Teacher类的属性，如teaName等
    schdirtea = internship.schdirtea
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    comdirtea = ComDirTea.query.filter_by(stuId=stuId, comId=comId).all()
    checktea = None
    if internship.icheckTeaId :
        checktea = Teacher.query.filter_by(teaId=internship.icheckTeaId).first()
    #实习协议图片路径
    path=[]
    name=[]
    p=os.path.join(os.path.abspath('.'),"app/static/storage/%s/agreement"%internId)
    if os.path.exists(p):
        for x in os.listdir(p):
            path.append(os.path.join(p[p.find('/static'):],x))
            name.append(x)
    path=zip(name,path)
    # 导出实习excel表
    intern_excel = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(ComInfor,
                                                                                                    InternshipInfor.comId == ComInfor.comId).outerjoin(
        Teacher, Teacher.teaId == InternshipInfor.icheckTeaId) \
        .filter(InternshipInfor.Id == internId) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, ComInfor.comId,
                     InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                     InternshipInfor.internCheck, InternshipInfor.task, InternshipInfor.post, Teacher.teaName,
                     InternshipInfor.opinion, InternshipInfor.icheckTime)
    # 若普通老师为学生的指导老师, 赋予其权限
    schdirtea_can = is_schdirtea(stuId)
    if request.method == "POST":
        if 'download' in request.form:
                #file_name=secure_filename(request.form.get('download'))
                file_name=request.form.get('download')
                return send_file(os.path.join(STORAGE_FOLDER,internId,'agreement',file_name), as_attachment=True,
                             attachment_filename=file_name.encode('utf-8'))
        if 'rename' in request.form:
            old_name=request.form.get("old_name")
            new_name=os.path.join(STORAGE_FOLDER,internId,'agreement',request.form.get("new_name").strip())
            print(type(request.form.get("new_name").strip()))
            if request.form.get("new_name").strip()!='':                                                
                os.rename(os.path.join(STORAGE_FOLDER,internId,'agreement',old_name),new_name)
                flash("重命名成功！")
                return redirect(url_for('.xIntern',internId=internId,stuId=stuId))
            else:
                flash("重命名失败！")
        if current_user.roleId == 0 or current_user.can(Permission.STU_INTERN_SEARCH) or schdirtea_can:
            isexport = request.form.get('isexport')
            if isexport:
                file_path = excel_export(excel_export_intern, intern_excel)
                return export_download(file_path)
    return render_template('xIntern.html', Permission=Permission, comInfor=comInfor, comdirtea=comdirtea, internship=internship, student=student, schdirtea_can=schdirtea_can, path=path, checktea=checktea,schdirtea=schdirtea)


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
    return redirect(url_for('.xIntern', stuId=stuId,internId=internId))

#修改实习信息前，先获得原来的实习信息
@main.route('/getIntern_json',methods=['GET'])
@login_required
def getIntern_json():
    if request.args.get('stuId'):
        stuId = request.args.get('stuId')
        internId = request.args.get('internId')
    else:
        stuId = request.args.get('stuId')
        internId = request.args.get('internId')
    if current_user.roleId == 0:
        stuId = current_user.stuId
    elif not current_user.can(Permission.STU_INTERN_EDIT):
        if is_schdirtea(stuId) is not True:
            flash('非法操作')
            return redirect('/')
    try:
        comId = InternshipInfor.query.filter_by(Id=internId).first().comId
        # student = Student.query.filter_by(stuId=stuId).first()
        internship = InternshipInfor.query.filter_by(Id=internId).first()
        # comInfor = ComInfor.query.filter_by(comId=comId).first()
        schdirtea = internship.schdirtea
        comdirtea = ComDirTea.query.filter_by(stuId=stuId, comId=comId).all()
        intern_json={}
        intern_json.setdefault('intern',{})
        intern_json.setdefault('ctea',[])
        intern_json.setdefault('tea',[])
        intern_json['intern'].update({'task':str(internship.task),'post':str(internship.post),'start':str(internship.start),'end':str(internship.end)})
        for x in comdirtea:
            intern_json['ctea'].append([x.cteaName,x.cteaDuty,x.cteaPhone,x.cteaEmail])
        for x in schdirtea:
            intern_json['tea'].append([x.teaName])
    except Exception as e:
        print('getIntern_json:',e)
    return json.dumps(intern_json)


# 修改实习信息
@main.route('/xInternEdit', methods=['GET', 'POST'])
@login_required
def xInternEdit():
    if request.args.get('stuId'):
        stuId = request.args.get('stuId')
        internId = request.args.get('internId')
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
    iform = internshipForm()
    # #校内指导老师提示列表
    teachers=Teacher.query.all()
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
        try:
            #修改校内指导老师
            internship=InternshipInfor.query.filter_by(Id=internId).first()
            old_teaName = request.form.getlist('old_teaName')
            for x in old_teaName:
                old_teacherId=Teacher.query.filter_by(teaName=x).first().teaId
                db.session.execute("delete from SchDirTea where internId=%s and teaId=%s"%(internId,old_teacherId))
                # internship.schdirtea.remove(old_teacher)
            i=0
            while True:
                i = i + 1
                teaValue = request.form.get('teaName%s' % i)
                if teaValue:
                    tea=Teacher.query.filter_by(teaName=teaValue).first()
                    if tea:
                        internship.schdirtea.append(tea)
                    else:
                        tea=Teacher.query.filter_by(teaName='无该用户').first()
                        internship.schdirtea.append(tea)
                else:
                    break
            #修改实习信息
            internship.task=iform.task.data
            internship.post=iform.post.data
            internship.start=iform.start.data
            internship.end=iform.end.data
            internship.time=datetime.now()
            db.session.add(internship)
            #修改企业指导老师
            #校外指导老师
            ComDirTeas=ComDirTea.query.filter_by(comId=comId).filter_by(stuId=stuId).all()
            for x in ComDirTeas:
                db.session.delete(x)
            j=0
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
            db.session.commit()
            # 实习信息修改,日志跟随变动
            journal_migrate(internId)

            #上传协议书
            if request.files.getlist('image')[0].filename!="":
                for i in request.files.getlist('image'):
                    i.save('%s/%s/agreement/%s' % (STORAGE_FOLDER, internId,i.filename))
            flash('修改成功！')
        except Exception as e:
            db.session.rollback()
            flash("修改失败！")
            print("修改实习信息：",e)
            return redirect(url_for(".xInternEdit",stuId=stuId,internId=internId))
        #邮件通知
        if current_user.roleId==0:
            stu=Student.query.filter_by(stuId=stuId).first()
            stuName=stu.stuName
            schdirtea = internship.schdirtea
            for tea in schdirtea:
                if tea.teaEmail:
                    teaName=tea.teaName
                    teaEmail=tea.teaEmail
                    body='%s老师:你好,学号为%s,姓名为%s,修改了实习信息!请登录东莞理工学院计算机与网络安全学院实习管理系统进行审核.' %(teaName,stuId,stuName)
                    html='%s老师:<p>你好,学号为%s,姓名为%s,修改了实习信息!</p><p>请登录<a href="http://shixi.dgut.edu.cn">东莞理工学院计算机与网络安全学院实习管理系统</a>进行审核.</p>'%(teaName,stuId,stuName)
                    try:
                        send_email(teaEmail,body,html)
                        return redirect(url_for('.xIntern',stuId=stuId,internId=internId))
                    except Exception as e:
                        print("实习信息修改邮件通知",e) 
                        return redirect(url_for('.xIntern',stuId=stuId,internId=internId)) 
        return redirect(url_for('.xIntern',stuId=stuId,internId=internId)) 
    return render_template('xStuInternEdit.html', Permission=Permission,internId=internId,stuId=stuId,imageName=imageName,iform=iform,teachers=teachers,comId=comId)



# 实习,日志,总结成果的单个删除
@main.route('/intern_delete', methods=['POST'])
@login_required
def comfirmDeletreJournal_Intern():
    internId = request.form.get('internId')
    from_url = request.form.get('from_url')
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    permission = False
    if current_user.roleId == 0 :
        if internship.internCheck!=2:
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
    if permission:
        try:
            if from_url == 'xSum':
                db.session.execute('delete from Summary where internId=%s' % internId)
            # 企业指导老师,日志,实习一同删除
            comId = InternshipInfor.query.filter_by(Id=internId).first().comId
            db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s' % (stuId, comId))
            db.session.execute('delete from SchDirTea where internId=%s'% internId)
            db.session.execute('delete from Journal where internId=%s and stuId=%s' % (internId, stuId))
            db.session.execute('delete from InternshipInfor where Id=%s and stuId=%s' % (internId, stuId))
            db.session.execute('delete from Visit_Intern where internId=%s'%(internId))
            # 企业累计实习人数减一
            db.session.execute('update ComInfor set students = students -1 where comId=%s' % comId)
            # 删除总结成果--文件目录
            subprocess.call('rm %s/%s -r' % (STORAGE_FOLDER, internId), shell=True)
            #删除pdf在线阅览文件
            subprocess.call('rm %s/%s -r' % (PDF_FOLDER, internId), shell=True)
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
            fpath = excel_export(excel_export_com, ComInfor.query.filter_by(comId=id).all())
            return export_download(fpath)
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
        cominfor = ComInfor.query.order_by(ComInfor.comDate.desc()).all()
        for c in cominfor:
            if c.comName.find(key.strip()) != -1:
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
            if intern.stuName == form.key.data.strip():
                internList.append(intern)
            if intern.stuId == form.key.data.strip():
                internList.append(intern)
            if intern.comName.find(form.key.data.strip()) != -1:
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
            if intern.stuName == form.key.data.strip():
                internList.append(intern)
            if intern.stuId == form.key.data.strip():
                internList.append(intern)
            if intern.comName.find(form.key.data.strip()) != -1:
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
            if intern.stuId == form.key.data.strip():
                internList.append(intern)
            if intern.stuName == form.key.data.strip():
                internList.append(intern)
            if intern.comName.find(form.key.data.strip()) != -1:
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
                if t.teaName == form.key.data.strip():
                    teacher.append(t)
                if t.teaId == form.key.data.strip():
                    teacher.append(t)
        else:
            stu = Student.query.all()
            for s in stu:
                if s.stuId == form.key.data.strip():
                    student.append(s)
                if s.stuName == form.key.data.strip():
                    student.append(s)
    return render_template("userSearchResult.html", Permission=Permission, student=student, tea=tea, teacher=teacher,
                           form=form, key=form.key.data, snum=len(student), tnum=len(teacher))



# 管理员\普通教师\审核教师
# 特定企业的实习学生列表
@main.route('/comInternList', methods=['GET', 'POST'])
@login_required
def comInternList():
    comId = request.args.get('comId')
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    comName = ComInfor.query.filter(ComInfor.comId == comId).first().comName
    # filter过滤当前特定企业ID
    pagination = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId) \
            .add_columns(InternshipInfor.Id, InternshipInfor.comId, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.stuId
                    ,Student.stuName, Student.grade, Student.classes, Student.major) \
            .filter(InternshipInfor.comId == comId) \
            .order_by(Student.grade).paginate(page, per_page=8, error_out=False)
    internship = pagination.items
    # for stu in student:
        # internStatus = InternshipInfor.query.filter_by(comId=comId, stuId=stu.stuId, internStatus=0).count()
        # session[stu.stuId] = internStatus
    return render_template('comInternList.html', form=form, pagination=pagination, internship=internship, Permission=Permission,
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
            com = ComInfor.query.filter_by(comId=comId).first()
            if check == 'pass':
                com.comCheck = 2
                str = '审核成功，一条信息审核通过。'
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
        flash("权限不足！")
        return redirect(url_for('.interncompany'))
    else:
        if request.method == 'POST':
            comId = str(request.form.get('comId'))
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
        com.comCity=comform.comCity.data
        com.comAddress = comform.comAddress.data
        com.comUrl = comform.comUrl.data
        com.comBrief = request.form.get('brief')
        com.comProject = request.form.get('project')
        com.comMon = comform.comMon.data
        com.comStaff = comform.comStaff.data
        com.comContact = comform.comContact.data
        com.comPhone = comform.comPhone.data
        com.comEmail = comform.comEmail.data
        com.comFax = comform.comFax.data
        com.comDate = datetime.now().date()
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
                db.session.rollback()
                print('message:', e)
                flash('error!!!')
                return redirect('/')
        internship = InternshipInfor.query.filter_by(stuId=stuId).count()
        if internship == 0:
            flash('目前还没有实习信息, 请先完善相关实习信息')
            return redirect('/')
        else:
            pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId == ComInfor.comId).join(Journal, InternshipInfor.Id == Journal.internId).join(
                Student, InternshipInfor.stuId == Student.stuId) \
                    .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId,
                                 InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end,
                                 InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.jourCheck) \
                    .filter(InternshipInfor.stuId == stuId).group_by(
                    InternshipInfor.Id).order_by(func.field(InternshipInfor.internStatus, 1, 0, 2)).paginate(page, per_page=8,  error_out=False)
            internlist = pagination.items
            return render_template('stuJournalList.html', form=form, internlist=internlist, Permission=Permission,
                                       pagination=pagination, grade=grade, major=major, classes=classes)
    elif current_user.can(Permission.STU_JOUR_SEARCH):
        intern = create_intern_filter(grade, major, classes, flag=1)
        pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId) \
            .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id,
                         InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus,
                         InternshipInfor.internCheck, InternshipInfor.jourCheck) \
            .filter(InternshipInfor.internCheck == 2, InternshipInfor.internStatus != 0).group_by(InternshipInfor.Id).order_by(
            func.field(InternshipInfor.internStatus, 1, 2)).paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        # 批量导出实习excel表
        if request.method == "POST" and current_user.can(Permission.STU_JOUR_EDIT):
            isexport = request.form.get('isexport')
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
    internId = request.args.get('internId')
    #防sql注入
    if current_user.roleId == 0:
        stuId = current_user.stuId
        if stuId!=InternshipInfor.query.filter_by(Id=internId).first().stuId:
            flash('非法操作！')
            return redirect('/')
    else:
        stuId = request.args.get('stuId')
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    comId = internship.comId
    #指导老师审核权限
    comfirm_can=is_schdirtea(stuId) or current_user.can(Permission.STU_JOUR_CHECK)
    comInfor = ComInfor.query.filter_by(comId=comId).first()
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
                               student=student, comInfor=comInfor, pagination=pagination, page=page, now=now,comfirm_can=comfirm_can)
    else:
        if internship.internCheck == 2:
            return render_template('xJournal.html', Permission=Permission, internship=internship, journal=journal,
                                   student=student, comInfor=comInfor, pagination=pagination, page=page, now=now,comfirm_can=comfirm_can)
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
    if current_user.can(Permission.STU_JOUR_CHECK) or is_schdirtea(stuId):
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
        return redirect(url_for('.xJournal',stuId=stuId,internId=internId))
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
    page = request.args.get('page')
    jourform = journalForm()
    if jour.jourCheck == 1 and current_user.roleId != 3:
        flash('日志已通过审核,无法修改')
        return redirect('/')
    return render_template('xJournalEdit.html', Permission=Permission, jour=jour, student=student, comInfor=comInfor,
                           internship=internship, jourform=jourform, page=page)
def htmlEscape(data):
    if data:
        data=data.replace("&","&amp;")
        data=data.replace("<","&lt;")
        data=data.replace(">","&gt;")
        data=data.replace("'","&apos;")
        data=data.replace("\"","&quot;")
    return data


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
    mon = htmlEscape(request.form.get('mon'))
    tue = htmlEscape(request.form.get('tue'))
    wed = htmlEscape(request.form.get('wed'))
    thu = htmlEscape(request.form.get('thu'))
    fri = htmlEscape(request.form.get('fri'))
    sat = htmlEscape(request.form.get('sat'))
    sun = htmlEscape(request.form.get('sun'))
    stuId = request.form.get('stuId')
    internId = request.form.get('internId')
    page = request.form.get('page')
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
        db.session.rollback()
        print(datetime.now(), ": 学号为", stuId, "修改日志失败", e)
        flash("修改日志失败")
        return redirect("/")
    try:
        stu=Student.query.filter_by(stuId=stuId).first()
        stuName=stu.stuName
        # internId=InternshipInfor.query.filter_by(stuId=stuId).first().Id
        internship = InternshipInfor.query.filter_by(Id=internId).first()
        schdirtea = internship.schdirtea
        for tea in schdirtea:
            if tea.teaEmail:
                teaName=tea.teaName
                teaEmail=tea.teaEmail
                body='%s老师:你好,学号为%s,姓名为%s,编辑了实习日志!请登录东莞理工学院计算机与网络安全学院实习管理系统进行审核.' %(teaName,stuId,stuName)
                html='%s老师:<p>你好,学号为%s,姓名为%s,编辑了实习日志!</p><p>请登录<a href="http://shixi.dgut.edu.cn">东莞理工学院计算机与网络安全学院实习管理系统</a>进行审核.</p>'%(teaName,stuId,stuName)
                send_email(teaEmail,body,html)

    except Exception as e:
        print('邮件发送异常:',e)
    flash("修改日志成功")
    return redirect(url_for('.xJournal', stuId=stuId, internId=internId,jourId=jourId, page=page))


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
    myStudent=request.args.get('myStudent')
    if myStudent:
        session['grade']=None
        session['major'] = None
        session['classes'] = None
        session['internStatus'] = None
        session['checkStatus'] = None


    elif grade is not None:
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
        session['myStudent']=None
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
    myStudent=request.args.get('myStudent')
    if myStudent:
        session['grade']=None
        session['major'] = None
        session['classes'] = None
        session['sex'] = None
        session['internStatus'] = None

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
        session['myStudent']=None
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
        return redirect(url_for('.selectStudent',filename=request.args.get('filename')))


# 添加学生用户
@main.route('/addStudent', methods=['GET', 'POST'])
@login_required
def addStudent():
    # 非管理员,不能进入
    if not current_user.can(Permission.STU_INTERN_MANAGE):
        return redirect('/')
    # user=Teacher.query.filter_by(teaId=current_user.teaId).first()
    stuform = stuForm()
    # schdirteaform = schdirteaForm()
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
    schdirteaform = schdirteaForm()
    stuId = request.args.get('stuId')
    stu = Student.query.filter_by(stuId=stuId).first()
    grade=Grade.query.all()
    classes=Classes.query.all()
    major=Major.query.all()
    if request.method == 'POST':
        try:
            #form
            stu.stuId = form.stuId.data
            stu.stuName = form.stuName.data
            stu.sex = request.form.get('sex')
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
    return render_template('editStudent.html', Permission=Permission, form=form, stu=stu,classes=classes,major=major,grade=grade)


# 单条删除学生用户信息
@main.route('/student_delete', methods=['GET', 'POST'])
@login_required
def student_delete():
    if current_user.can(Permission.STU_INTERN_MANAGE):
        stuId = request.form.get('stuId')
        internship = InternshipInfor.query.filter_by(stuId=stuId).all()
        try:
            db.session.execute('delete from Student where stuId="%s"'%stuId)
            for i in internship:
                db.session.execute('delete from Journal where stuId="%s"'%i.Id)
                db.session.execute('delete from ComDirTea where internId=%s'%i.Id)
                db.session.execute('delete from SchDirTea where internId=%s'%i.Id)
                db.session.execute('delete from Summary where internId=%s'%i.Id)
                db.session.execute('delete from Visit_Intern where internId=%s'%i.Id)
                db.session.delete(i)
                # 删除总结成果--文件目录
                subprocess.call('rm %s/%s -r' % (STORAGE_FOLDER, i.Id), shell=True)
                #删除pdf在线阅览文件
                subprocess.call('rm %s/%s -r' % (PDF_FOLDER, i.Id), shell=True)
                db.session.delete(i)
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
    if teaId:
        # 同上
        tea = []
        tea.append(teaId)
        session['tea'] = tea
    # 点击选择后发生
    if roleId:
        # 学生
        if session.get('stu'):
            for stuId in session['stu']:
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
                stuId=x
                internship = InternshipInfor.query.filter_by(stuId=stuId).all()
                db.session.execute('delete from Student where stuId="%s"'%stuId)
                for i in internship:
                    db.session.execute('delete from Journal where stuId="%s"'%i.Id)
                    db.session.execute('delete from ComDirTea where internId=%s'%i.Id)
                    db.session.execute('delete from SchDirTea where internId=%s'%i.Id)
                    db.session.execute('delete from Summary where internId=%s'%i.Id)
                    db.session.execute('delete from Visit_Intern where internId=%s'%i.Id)
                    db.session.delete(i)
                    # 删除总结成果--文件目录
                    subprocess.call('rm %s/%s -r' % (STORAGE_FOLDER, i.Id), shell=True)
                    #删除pdf在线阅览文件
                    subprocess.call('rm %s/%s -r' % (PDF_FOLDER, i.Id), shell=True)
                    db.session.delete(i)
                db.session.commit()
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
        tea = Teacher(teaName=form.teaName.data, teaId=form.teaId.data, teaSex=form.teaSex.data,teaEmail=form.teaEmail.data,teaPhone=form.teaPhone.data,teaPosition=form.teaPosition.data)
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
    #普通教师基本信息修改
    if request.method == 'POST':
        try:
            tea.teaId = form.teaId.data
            tea.teaName = form.teaName.data
            tea.teaSex = request.form.get('sex')
            tea.teaEmail=form.teaEmail.data
            tea.teaPhone=form.teaPhone.data
            tea.teaPosition=form.teaPosition.data
            db.session.add(tea)
            db.session.commit()
            flash('修改成功！')
            if current_user.can(Permission.TEA_INFOR_MANAGE):
                return redirect(url_for('.teaUserList'))
            else:
                return redirect(url_for('.index'))
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
            a = eval(form.COM_INFOR_SEARCH.description) | a
        if form.COM_INFOR_EDIT.data:
            a = eval(form.COM_INFOR_EDIT.description) | a
        if form.COM_INFOR_CHECK.data:
            a = eval(form.COM_INFOR_CHECK.description) | a
        if form.INTERNCOMPANY_LIST.data:
            a = eval(form.INTERNCOMPANY_LIST.description) | a
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
        if form.ALTER_INTRODUCE.data:
            a = eval(form.ALTER_INTRODUCE.description) | a
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
            db.session.rollback()
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
            a = eval(form.COM_INFOR_SEARCH.description) | a
        if form.COM_INFOR_EDIT.data:
            a = eval(form.COM_INFOR_EDIT.description) | a
        if form.COM_INFOR_CHECK.data:
            a = eval(form.COM_INFOR_CHECK.description) | a
        if form.INTERNCOMPANY_LIST.data:
            a = eval(form.INTERNCOMPANY_LIST.description) | a
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
        if form.ALTER_INTRODUCE.data:
            a = eval(form.ALTER_INTRODUCE.description) | a
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

    if request.args.get('name') is not None:
        session['name'] = request.args.get('name')

    if request.args.get('students') is not None:
        session['students'] = request.args.get('students')

    if request.args.get('status') is not None:
        session['status'] = request.args.get('status')
    i = 0
    # 组合查询 *_*
    try:
        if session.get('city') is not None:
            print('city:', session['city'])
            com = ComInfor.query.filter_by(comCity=session['city'])

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

            if session.get('status') is not None:
                if flag:
                    if session['status'] == '2':
                        com = com.filter_by(comCheck=2)
                    else:
                        com = com.filter(ComInfor.comCheck != 2)
                else:
                    if session['status'] == '1':
                        com = com.filter_by(comCheck=1)
                    else:
                        com = com.filter_by(comCheck=0)
            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    citys = db.session.execute('select DISTINCT comCity from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comCity from ComInfor WHERE comCheck=2')
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
                    else:
                        com = com.filter_by(comCheck=0)
            if session.get('city') is not None:
                com = com.filter_by(comCity=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    citys = db.session.execute('select DISTINCT comCity from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comCity from ComInfor WHERE comCheck=2')
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
                    else:
                        com = com.filter_by(comCheck=0)
            if session.get('city') is not None:
                com = com.filter_by(comCity=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    citys = db.session.execute('select DISTINCT comCity from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comCity from ComInfor WHERE comCheck=2')
        elif session.get('status') is not None:
            if flag:
                if session['status'] == '2':
                    com = ComInfor.query.filter_by(comCheck=2)
                else:
                    com = ComInfor.query.filter(ComInfor.comCheck != 2)
            else:
                if session['status'] == '1':
                    com = ComInfor.query.filter_by(comCheck=1)
                else:
                    com = ComInfor.query.filter_by(comCheck=0)

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
                com = com.filter_by(comCity=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    citys = db.session.execute('select DISTINCT comCity from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comCity from ComInfor WHERE comCheck=2')
        else:
            if flag:
                if current_user.can(Permission.COM_INFOR_EDIT):
                    com = ComInfor.query.order_by(ComInfor.comDate.desc())
                    citys = db.session.execute('select DISTINCT comCity from ComInfor')
                else:
                    com = ComInfor.query.filter_by(comCheck=2).order_by(ComInfor.comDate.desc())
                    citys = db.session.execute('select DISTINCT comCity from ComInfor WHERE comCheck=2')
            else:
                com = ComInfor.query.filter(ComInfor.comCheck != 2).order_by(ComInfor.comDate.desc())
                citys = db.session.execute('select DISTINCT comCity from ComInfor WHERE comCheck!=2')
        if not flag:
            com = com.filter(ComInfor.comCheck != 2)
            citys = db.session.execute('select DISTINCT comCity from ComInfor WHERE comCheck!=2')
    except Exception as e:
        print('组合筛选：', e)
    # 生成筛选项
    for c in citys:
        city[i] = c.comCity
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
        print(session['grade'])

    if request.args.get('major') is not None:
        session['major'] = request.args.get('major')

    if request.args.get('classes') is not None:
        session['classes'] = request.args.get('classes')

    if request.args.get('internStatus') is not None:
        session['internStatus'] = request.args.get('internStatus')

    if request.args.get('checkStatus') is not None:
        session['checkStatus'] = request.args.get('checkStatus')

    if request.args.get('myStudent'):
        session['myStudent'] = request.args.get('myStudent')

    i = 0
    j = 0
    k = 0
    # 组合查询 *_*
    try:
        if session.get('grade'):
            if flag==2:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).outerjoin(Summary, Summary.internId == InternshipInfor.Id).filter(
                Student.grade == session['grade'])
            elif flag==1:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(Journal, InternshipInfor.Id == Journal.internId).filter(
                Student.grade == session['grade'])
            else:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).filter(
                Student.grade == session['grade'])

            if session.get('major'):
                intern = intern.filter(Student.major == session['major'])

            if session.get('classes'):
                intern = intern.filter(Student.classes == session['classes'])

            if session.get('internStatus'):
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])

            if session.get('checkStatus'):
                if flag == 2:
                    intern = intern.filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.filter_by(jourCheck=session['checkStatus'])
            if session.get('myStudent'):
                intern=intern.join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())

        elif session.get('major'):
            if flag==2:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).outerjoin(Summary, Summary.internId == InternshipInfor.Id).filter(Student.major == session['major'])
            elif flag==1:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(Journal, InternshipInfor.Id == Journal.internId).filter(Student.major == session['major'])
            else:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).filter(Student.major == session['major'])

            if session.get('grade'):
                intern = intern.filter(Student.grade == session['grade'])

            if session.get('classes'):
                intern = intern.filter_by(classes=session['classes'])

            if session.get('internStatus'):
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])

            if session.get('checkStatus'):
                if flag == 2:
                    intern = intern.filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor, InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.filter_by(jourCheck=session['checkStatus'])
            if session.get('myStudent'):
                intern=intern.join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())

        elif session.get('classes'):
            if flag==2:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).outerjoin(Summary, Summary.internId == InternshipInfor.Id).filter(Student.classes == session['classes'])
            elif flag==1:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(Journal, InternshipInfor.Id == Journal.internId).filter(Student.classes == session['classes'])
            else:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).filter(Student.classes == session['classes'])


            if session.get('grade'):
                intern = intern.filter(Student.grade == session['grade'])

            if session.get('major'):
                intern = intern.filter(Student.major == session['major'])

            if session.get('internStatus'):
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])

            if session.get('checkStatus'):
                if flag == 2:
                    intern = intern.filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.filter_by(
                        jourCheck=session['checkStatus'])
            if session.get('myStudent'):
                intern=intern.join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())

        elif session.get('internStatus') is not None:
            if flag==2:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).outerjoin(Summary, Summary.internId == InternshipInfor.Id).filter(InternshipInfor.internStatus == session['internStatus'])
            elif flag==1:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(Journal, InternshipInfor.Id == Journal.internId).filter(InternshipInfor.internStatus == session['internStatus'])
            else:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).filter(InternshipInfor.internStatus == session['internStatus'])

            if session.get('classes') is not None:
                intern = intern.filter(Student.classes == session['classes'])

            if session.get('grade') is not None:
                intern = intern.filter(Student.grade == session['grade'])

            if session.get('major') is not None:
                intern = intern.filter(Student.major == session['major'])

            if session.get('checkStatus') is not None:
                if flag == 2:
                    intern = intern.filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.filter_by(jourCheck=session['checkStatus'])
            if session.get('myStudent'):
                intern=intern.join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())

        elif session.get('checkStatus') is not None:
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

            if session.get('classes'):
                intern = intern.filter(Student.classes == session['classes'])

            if session.get('grade'):
                intern = intern.filter(Student.grade == session['grade'])

            if session.get('major'):
                intern = intern.filter(Student.major == session['major'])

            if session.get('internStatus'):
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])
            if session.get('myStudent'):
                intern=intern.join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())


        elif session.get('myStudent'):
            if flag==2:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).outerjoin(Summary, Summary.internId == InternshipInfor.Id).join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())
            elif flag==1:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(Journal, InternshipInfor.Id == Journal.internId).join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())
            else:
                intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())
            if session.get('major') is not None:
                intern = intern.filter(Student.major == session['major'])

            if session.get('classes') is not None:
                intern = intern.filter(Student.classes == session['classes'])

            if session.get('internStatus') is not None:
                intern = intern.filter(InternshipInfor.internStatus == session['internStatus'])
            if session.get('checkStatus') is not None:
                if flag == 2:
                    intern = intern.filter(Summary.sumCheck == session['checkStatus'])
                elif flag == 0:
                    intern = intern.filter(InternshipInfor.internCheck == session['checkStatus'])
                else:
                    intern = intern.filter_by(jourCheck=session['checkStatus'])

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
    os.system('mkdir %s/%s' % (PDF_FOLDER,internId))
    os.system('mkdir %s/%s/attachment' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/summary_doc' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/attachment' % (PDF_FOLDER, internId))
    os.system('mkdir %s/%s/summary_doc' % (PDF_FOLDER, internId))
    os.system('mkdir %s/%s/score_img' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/agreement' % (STORAGE_FOLDER, internId))
    os.system('mkdir %s/%s/visit' % (STORAGE_FOLDER, internId))
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
        for x in range(end_isoyear - start_isoyear):
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
def create_stu_filter(grade, major, classes,my={}):
    # 更新筛选项
    #判断是否选择我的学生
    if request.args.get('grade') is not None:
        session['grade'] = request.args.get('grade')

    if request.args.get('major') is not None:
        session['major'] = request.args.get('major')

    if request.args.get('classes') is not None:
        session['classes'] = request.args.get('classes')

    if request.args.get('sex') is not None:
        session['sex'] = request.args.get('sex')
    if request.args.get('myStudent'):
        session['myStudent'] = request.args.get('myStudent')
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
            if session.get('myStudent'):
                my[0]=True
                stu=stu.join(InternshipInfor,InternshipInfor.stuId==Student.stuId).join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())

        elif session.get('major') is not None:
            stu = Student.query.filter_by(major=session['major'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])

            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])
            if session.get('myStudent'):
                my[0]=True
                stu=stu.join(InternshipInfor,InternshipInfor.stuId==Student.stuId).join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())


        elif session.get('classes') is not None:
            stu = Student.query.filter_by(classes=session['classes'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])
            if session.get('myStudent'):
                my[0]=True
                stu=stu.join(InternshipInfor,InternshipInfor.stuId==Student.stuId).join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())



        elif session.get('sex') is not None:
            stu = Student.query.filter_by(sex=session['sex'])

            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])
            if session.get('myStudent'):
                my[0]=True
                stu=stu.join(InternshipInfor,InternshipInfor.stuId==Student.stuId).join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())

        elif session.get('myStudent'):
            my[0]=True
            stu=Student.query.join(InternshipInfor,InternshipInfor.stuId==Student.stuId).join(SchDirTea).join(Teacher).filter(Teacher.teaId==current_user.get_id())
            if session.get('grade') is not None:
                stu = stu.filter_by(grade=session['grade'])

            if session.get('major') is not None:
                stu = stu.filter_by(major=session['major'])

            if session.get('classes') is not None:
                stu = stu.filter_by(classes=session['classes'])
            if session.get('sex') is not None:
                stu = stu.filter_by(sex=session['sex'])
        else:
            stu = Student.query.order_by(Student.grade.asc())
    except Exception as e:
        print('组合筛选：', e)
    # 生成筛选项
    grades = db.session.execute('select DISTINCT grade from Grade order by grade desc')
    majors = db.session.execute('select DISTINCT major from Major')
    classess = db.session.execute('select DISTINCT classes from Classes ORDER BY classes')
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

# 查询最大的探访记录visitId
def getMaxVisitId():
    res = db.session.query(func.max(Visit.visitId).label('max_visitId')).one()
    return res.max_visitId


# ---------------Excel表格导入导出-----------------------------------------------

# Excel文档列名的模板. 导入和导出
# 实习信息表
excel_export_intern = OrderedDict((('stuId', '学号'), ('stuName', '姓名'), ('comCity', '城市'), ('comName', '企业名称'),
                                   ('internCheck', '审核状态'), ('internStatus', '实习状态'), ('start', '开始日期'),
                                   ('end', '结束日期'), ('task', '任务'),  ('post', '岗位'), ('teaName', '审核教师'), ('opinion', '审核意见'),
                                   ('icheckTime', '审核时间'), ('time', '修改时间'), ('steaName', '校内指导老师姓名'), ('steaPosition', '校内指导老师职务'),
                                   ('steaPhone', '校内指导老师电话'), ('steaEmail', '校内指导老师邮箱'), ('cteaName', '企业指导老师姓名'),
                                   ('cteaDuty', '企业指导老师职务'), ('cteaPhone', '企业指导老师电话'), ('cteaEmail', '企业指导老师邮箱')))
excel_import_intern = {'学号': 'stuId', '姓名': 'stuName', '企业编号': 'comId', '开始日期': 'start', '结束日期': 'end',
                       '任务': 'task', '岗位': 'post', '企业指导老师姓名': 'cteaName', '企业指导老师职务': 'cteaDuty', '企业指导老师电话': 'cteaPhone', '企业指导老师邮箱': 'cteaEmail'}
# 企业信息表
excel_export_com = OrderedDict((('comId', '企业编号'), ('comName', '企业名称'), ('comCity', '城市'), ('comBrief', '企业简介'), ('comAddress', '地址'),
                                ('comUrl', '网站'), ('comMon', '营业额'), ('comContact', '联系人'), ('comDate', '录入时间'),
                                ('comProject', '企业项目'), ('comStaff', '员工人数'), ('comPhone', '电话'), ('comEmail', '邮箱'),
                                ('comFax', '传真'), ('comCheck', '审核状态'), ('students', '实习学生人数')))
excel_import_com = {'企业名称': 'comName', '企业简介': 'comBrief', '城市': 'comCity', '地址': 'comAddress', '网站': 'comUrl', '营业额': 'comMon',
                    '联系人': 'comContact', '录入时间': 'comDate', '企业项目': 'comProject', '员工人数': 'comStaff', '电话': 'comPhone',
                    '邮箱': 'comEmail', '传真': 'comFax'}

# 日志表
# 实习详情
excel_export_journal_internDetail =  OrderedDict((('stuId', '学号'), ('stuName', '姓名'), ('comName', '企业名称'), ('comCity', '企业城市'), ('major','专业班级'), ('start','实习期间')))
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

excel_import_teaUser = {'教工号': 'teaId', '姓名': 'teaName', '性别': 'teaSex', '职称':'teaPosition', '邮箱': 'teaEmail', '电话':'teaPhone'}


IMPORT_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/xls_import')
EXPORT_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/xls_export')
IMPORT_TEMPLATE_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/import_template')
EXPORT_ALL_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/all_export')
VISIT_EXPORT_ALL_FOLDER = os.path.join(os.path.abspath('.'), 'file_cache/visit_export')



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
# multiple internship can export to one .xls
def journal_export(internIdList):
    template_A = excel_export_journal_internDetail
    template_B = excel_export_journal_log
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet 1', cell_overwrite_ok=True)
    row = 0
    for internId in internIdList:
        intern = InternshipInfor.query.join(Student, Student.stuId == InternshipInfor.stuId).join(ComInfor, ComInfor.comId == InternshipInfor.comId).add_columns(InternshipInfor.stuId, InternshipInfor.start, InternshipInfor.end, Student.stuName, Student.major, Student.classes, ComInfor.comName, ComInfor.comCity).filter(InternshipInfor.Id == internId).first()
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
            else:
                ws.write(row+1, col, (str(getattr(intern, colname))) )
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
    file_name = 'journalList_export_%s.xls' % random.randint(1,1000)
    file_path = os.path.join(EXPORT_FOLDER, file_name)
    wb.save(file_path)
    return file_path


# 导出Excel, 多个指导老师合并在一个单元格上
def multiDirTea_dict(tb_name):
    if tb_name in ['SchDirTea', 'ComDirTea']:
        multiDirTea_dict = {}
        # 校内导师
        if tb_name == 'SchDirTea':
            multiDirTea = db.session.execute('select * from SchDirTea left join Teacher on SchDirTea.teaId=Teacher.teaId group by internId having count(internId)>1')
            # multiDirTea = db.session.execute('select * from SchDirTea group by internId having count(internId) > 1;')
            for x in multiDirTea:
                # schdirtea = Teacher.query.filter_by(teaId=x.teaId).first()
                if not multiDirTea_dict.get(x.internId):
                    multiDirTea_dict[x.internId] = {'teaName': x.teaName, 'teaPosition': x.teaPosition,
                                                 'teaEmail': x.teaEmail, 'teaPhone': x.teaPhone}
                    for xx in multiDirTea_dict[x.internId]:
                        if multiDirTea_dict[x.internId].get(xx) is None:
                            multiDirTea_dict[x.internId][xx] = '未知'
                else:
                    multiDirTea_dict[x.internId] = { \
                        'teaName': multiDirTea_dict[x.internId]['teaName'] + '/%s' % x.teaName, \
                        'teaPosition': multiDirTea_dict[x.internId]['teaPosition'] + '/%s' % x.teaPosition, \
                        'teaEmail': multiDirTea_dict[x.internId]['teaEmail'] + '/%s' % x.teaEmail, \
                        'teaPhone': multiDirTea_dict[x.internId]['teaPhone'] + '/%s' % x.teaPhone \
                        }

                # if not multiDirTea_dict.get(x.stuId):
                #     multiDirTea_dict[x.stuId] = {'steaName': x.steaName, 'steaDuty': x.steaDuty,
                #                                  'steaEmail': x.steaEmail, 'steaPhone': x.steaPhone}
                #     for xx in multiDirTea_dict[x.stuId]:
                #         if multiDirTea_dict[x.stuId].get(xx) is None:
                #             multiDirTea_dict[x.stuId][xx] = '未知'
                # else:
                #     multiDirTea_dict[x.stuId] = { \
                #         'steaName': multiDirTea_dict[x.stuId]['steaName'] + '/%s' % x.steaName, \
                #         'steaDuty': multiDirTea_dict[x.stuId]['steaDuty'] + '/%s' % x.steaDuty, \
                #         'steaEmail': multiDirTea_dict[x.stuId]['steaEmail'] + '/%s' % x.steaEmail, \
                #         'steaPhone': multiDirTea_dict[x.stuId]['steaPhone'] + '/%s' % x.steaPhone \
                #         }
        # 企业导师
        elif tb_name == 'ComDirTea':
            # multiDirTea = db.session.execute(
            #     'select * from %s where stuId in (select stuId from %s group by stuId having count(stuId) > 1)' % (
            #         tb_name, tb_name))
            multiDirTea = db.session.execute('select * from ComDirTea group by stuId having count(stuId) > 1')
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

'''
def excel_export_intern_teacher(data):
    # def get_teacher_information(internId, flag):
    #     if flag == "SchDirTea":
    #         teachers = SchDirTea.query.join(Teacher, SchDirTea.teaId==Teacher.teaId)
    #         teachers = db.session.execute("select * from SchDirTea left join Teacher on SchDirTea.teaId=Teacher.teaId where SchDirTea.internId=%s" % internId)
    #         for teacher in teachers:
    internId_list = [x.Id for x in data]
    flagA = []
    teacher_dict = {}
    # temp = ''.join([',%s' % x for x in internId_list])
    # for x in db.session.execute("select * from SchDirTea where internId in (null,%s) group by internId having count(internId) > 1" %  ''.join([',%s' % x for x in internId_list])):
    teachers = db.session.execute('select * from SchDirTea left join Teacher on SchDirTea.teaId=Teacher.teaId where internId in (null,%s)' % ''.join([',%s' % internId for internId in internId_list]))
    for teacher in teachers:
        if teacher.internId in flagA:
            teacher_dict[str(teacher.internId)]['steaName'] = '/'.join(teacher_dict[str(teacher.internId)]['steaName'], teacher.teaName)
            teacher_dict[str(teacher.internId)]['steaPosition'] = '/'.join(teacher_dict[str(teacher.internId)]['steaPosition'], teacher.teaPosition)
            teacher_dict[str(teacher.internId)]['steaEmail'] = '/'.join(teacher_dict[str(teacher.internId)]['steaEmail'], teacher.teaEmail)
            teacher_dict[str(teacher.internId)]['steaPhone'] = '/'.join(teacher_dict[str(teacher.internId)]['steaPhone'], teacher.teaPhone)
        else:
            teacher_dict[str(teacher.internId)]['steaName'] = teacher.teaName
            teacher_dict[str(teacher.internId)]['steaPosition'] = teacher.teaPosition
            teacher_dict[str(teacher.internId)]['steaEmail'] = teacher.teaEmail
            teacher_dict[str(teacher.internId)]['steaPhone'] = teacher.teaPhone
        flagA.append(teacher.internId)
    for internship,index in zip(data, range(len(data))):
        internId = str(internship.Id)
        data[index]['steaName'] = teacher_dict[internId]['steaName']
        data[index]['steaPosition'] = teacher_dict[internId]['steaPosition']
        data[index]['steaEmail'] = teacher_dict[internId]['steaEmail']
        data[index]['steaPhone'] = teacher_dict[internId]['steaPhone']
    return data
'''

def joinMultiTeacher(internship,target):
    def getNoNone(foo):
        if foo:
            return foo
        else:
            return ""
    target_dict = {
            'steaName' : 'teaName',
            'steaPhone' : 'teaPhone',
            'steaPosition' : 'teaPosition',
            'steaEmail' : 'teaEmail'
            }
    internId = internship.Id
    schdirtea = db.session.execute("SELECT * FROM SchDirTea left join Teacher on SchDirTea.teaId=Teacher.teaId where internId=%s" % internId)
    multiTeacher = ""
    flag = False
    for x in schdirtea:
        if flag:
            multiTeacher = multiTeacher + '/' + getNoNone(getattr(x,target_dict[target]))
        else:
            flag = True
            multiTeacher = getNoNone(getattr(x,target_dict[target]))
    return multiTeacher





# 导出Excel
# 实习列表传入Basequery对象,企业列表传入list结果对象
def excel_export(template, data):
    # 实习列表再处理
    if template == excel_export_intern:
        # multiSchTea = multiDirTea_dict('SchDirTea')
        multiComTea = multiDirTea_dict('ComDirTea')
        data = data.outerjoin(ComDirTea, and_(
            ComDirTea.comId == InternshipInfor.comId, ComDirTea.stuId == InternshipInfor.stuId)) \
            .add_columns(
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
            elif colname in ['steaName','steaEmail','steaPhone','steaPosition']:
                ws.write(row+1,col,joinMultiTeacher(xdata,colname))
            else:
                if hasattr(xdata, colname):
                    ws.write(row + 1, col, str(getattr(xdata, colname)))
        # 若一学生存在多个导师
        if template == excel_export_intern:
        #     if xdata.internId in multiSchTea.keys():
        #         ws.write(row + 1, cols_list.index('teaName'), multiSchTea[xdata.internId]['teaName'])
        #         ws.write(row + 1, cols_list.index('teaPhone'), multiSchTea[xdata.internId]['teaPhone'])
        #         ws.write(row + 1, cols_list.index('teaPosition'), multiSchTea[xdata.internId]['teaPosition'])
        #         ws.write(row + 1, cols_list.index('teaEmail'), multiSchTea[xdata.internId]['teaEmail'])
            if xdata.stuId in multiComTea.keys():
                ws.write(row + 1, cols_list.index('cteaName'), multiComTea[xdata.stuId]['cteaName'])
                ws.write(row + 1, cols_list.index('cteaPhone'), multiComTea[xdata.stuId]['cteaPhone'])
                ws.write(row + 1, cols_list.index('cteaDuty'), multiComTea[xdata.stuId]['cteaDuty'])
                ws.write(row + 1, cols_list.index('cteaEmail'), multiComTea[xdata.stuId]['cteaEmail'])
    # 每个模板最多保存100份导出临时文件
    if template == excel_export_intern:
        file_name = 'internlist_export_%s.xls' % random.randint(1, 1000)
    elif template == excel_export_com:
        file_name = 'comlist_export_%s.xls' % random.randint(1, 1000)
    elif template == excel_export_stuUser:
        file_name = 'stuUserList_export_%s.xls' % random.randint(1, 1000)
    elif template == excel_export_teaUser:
        file_name = 'teaUserList_export_%s.xls' % random.randint(1, 1000)
    file_path = os.path.join(EXPORT_FOLDER, file_name)
    wb.save(file_path)
    return file_path

def export_all_file_list():
    # 根目录
    root_path = os.path.join(EXPORT_ALL_FOLDER, str(datetime.now().timestamp()))
    root_path_2 = os.path.join(root_path, '实习管理系统批量导出_%s' % datetime.now().date())
    visit_src = os.path.join(STORAGE_FOLDER, 'visit')
    file_list = []
    intern_org = InternshipInfor.query.join(Student, Student.stuId==InternshipInfor.stuId) \
        .join(ComInfor, ComInfor.comId==InternshipInfor.comId) \
        .outerjoin(Teacher, Teacher.teaId==InternshipInfor.icheckTeaId) \
        .filter(InternshipInfor.internStatus==2, InternshipInfor.internCheck==2) \
        .add_columns(InternshipInfor.Id, InternshipInfor.stuId, InternshipInfor.internCheck, InternshipInfor.internStatus, InternshipInfor.start, InternshipInfor.end, InternshipInfor.task, InternshipInfor.post, InternshipInfor.opinion, InternshipInfor.icheckTime, InternshipInfor.time, Student.stuName, Student.grade, Student.major, ComInfor.comName, ComInfor.comCity, Teacher.teaName)
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
    return file_list, root_path, root_path_2, visit_src



def get_export_all_update_status():
    def search_updated(update_time):
        result = {}
        temp_path = os.path.join(EXPORT_ALL_FOLDER, update_time)
        for x in os.listdir(temp_path):
           if x.split('.')[-1] == 'zip':
               file_path = os.path.join(temp_path, x)
               result['file_path'] = file_path
               update_time = datetime.fromtimestamp(float(update_time)).strftime('%Y-%m-%d %H:%M:%S')
               result['update_time'] = update_time
               return result
        return False
    is_exporting_all = False
    update_time_list = sorted(os.listdir(EXPORT_ALL_FOLDER))
    # 文件夹为空, 需要初始化
    if not update_time_list:
        return 'empty'
    temp = search_updated(update_time_list[-1])
    if not temp:
        # 第一个文件夹正在初始化
        if len(update_time_list) == 1:
            return 'initing'
        else:
            # if the compress was corrupted
            if time.time() - float(update_time_list[-1]) > 300:
                os.system('rm -r %s/%s' % (EXPORT_ALL_FOLDER, update_time_list[-1]))
            is_exporting_all = True
            temp = search_updated(update_time_list[-2])
    temp['is_exporting_all'] = is_exporting_all
    return temp

def get_export_all_generate():
    file_list, root_path, root_path_2, visit_src = export_all_file_list()
    with open('export_all.list','w') as f:
        f.write(str(file_list) + '\n')
        f.write('%s' % root_path + '\n')
        f.write('%s' % root_path_2 + '\n')
        f.write('%s' % visit_src)
    os.popen('python3 export_all.py&', 'r')


@main.route('/export_all_page', methods=['GET', 'POST'])
def export_all_page():
    if current_user.can(Permission.STU_INTERN_SEARCH) and current_user.can(Permission.STU_JOUR_SEARCH) and current_user.can(Permission.STU_SUM_SEARCH):
        update_status = get_export_all_update_status()
        if update_status is 'empty' :
            get_export_all_generate()
            return redirect(url_for('.export_all_page'))
        elif update_status is 'initing':
            update_time = False
            is_exporting_all = True
        else :
            update_time = update_status['update_time']
            is_exporting_all = update_status['is_exporting_all']
            updated_file_path = update_status['file_path']
            if request.method == 'POST':
                isdownload = request.form.get('isdownload')
                isupdate = request.form.get('isupdate')
                if isupdate:
                    get_export_all_generate()
                    return redirect(url_for('.export_all_page'))
                elif isdownload:
                    return send_file(updated_file_path, as_attachment=True, attachment_filename=updated_file_path.split('/')[-1].encode('utf-8'))
        return render_template('export_all_page.html', Permission=Permission, update_time=update_time, is_exporting_all=is_exporting_all)


# 导入excel表, 检查数据是否完整或出错
EXCEL_IMPORT_CHECK_STUINTERNLIST = ['stuId', 'stuName', 'comId', 'start', 'end']
EXCEL_IMPORT_CHECK_INTERNCOMPANY = ['comName', 'comAddress', 'comProject', 'comPhone', 'comEmail', 'comCity']
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


# 导入的Excel中, 统一将长串的float类型改为str
# 适用于学号,电话号码
def float2str(float_id):
    print (float_id)
    if re.match(r'.*\..*', float_id):
        str_id = str(float_id[:-2])
    else:
        str_id = float_id
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
                            start=start,
                            end=end,
                            task=intern['task'],
			    post=intern['post'],
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
                            for x in range(jour.workStart.isocalendar()[2] - 1, week_end.isocalendar()[2]):
                                which_day = week[x]
                                if journal[which_day]:
                                    db.session.execute('update Journal set %s = "%s" where internId=%s and weekNo=%s' % (which_day, journal[which_day], internId,  int(journal['weekNo'].split('.')[0])))

                elif from_url == 'interncompany':
                    comlist = excel_import(os.path.join(IMPORT_FOLDER, filename), excel_import_com, EXCEL_IMPORT_CHECK_INTERNCOMPANY)
                    if comlist is False:
                        return redirect('/')
                    for com, col in zip(comlist, range(len(comlist))):
                        if current_user.can(Permission.COM_INFOR_CHECK):
                             cominfor = ComInfor(
                                # 在资料导出时, comName作为文件名, 所以需要检查
                                comName = secure_comName(com['comName']),
                                comCity = com['comCity'],
                                comBrief = com['comBrief'],
                                comAddress = com['comAddress'],
                                comUrl = com['comUrl'],
                                # 使Excel生成的保留一位小数数字,变成保留到个位
                                comMon = str(com['comMon'])[:-2],
                                comContact = com['comContact'],
                                comDate = now,
                                comProject = com['comProject'],
                                comStaff = com['comStaff'],
                                comPhone = com['comPhone'],
                                comEmail = com['comEmail'],
                                comFax = com['comFax'],
                                comCheck = 2
                            )
                        else:
                            cominfor = ComInfor(
                                comName = com['comName'],
                                comCity = com['comCity'],
                                comBrief = com['comBrief'],
                                comAddress = com['comAddress'],
                                comUrl = com['comUrl'],
                                # 使Excel生成的保留一位小数数字,变成保留到个位
                                comMon = str(com['comMon'])[:-2],
                                comContact = com['comContact'],
                                comDate = now,
                                comProject = com['comProject'],
                                comStaff = com['comStaff'],
                                comPhone = com['comPhone'],
                                comEmail = com['comEmail'],
                                comFax = com['comFax'],
                                comCheck = 0
                            )
                        db.session.add(cominfor)

                elif from_url == 'stuUserList':
                    stuUserList = excel_import(os.path.join(IMPORT_FOLDER, filename), excel_import_stuUser, EXCEL_IMPORT_CHECK_STUUSERLIST)
                    if stuUserList is False:
                        return redirect('/')
                    # build the major option list
                    major_option_list = []
                    for x in Major.query.all():
                        major_option_list.append(x.major)
                    for stuUser, col in zip(stuUserList, range(len(stuUserList))):
                        ## 数据规范
                        ## 班级取数字, 不要'班'
                        #classes = re.findall(r'\d+', stuUser['classes'])[0]
                        ## 例'2014级'取'2014'
                        #grade = re.findall(r'\d+', stuUser['grade'])[0]
                        #major = stuUser['major']
                        #if len(grade) == 2:
                        #    grade = '20' + grade

                        # 班级取数字, 不要'班'
                        classes = re.findall(r'\d+', stuUser['classes'])
                        # 例'2014级'取'2014'
                        grade = re.findall(r'\d+', stuUser['grade'])
                        major = stuUser['major']
                        sex = stuUser['sex']
                        assert len(grade) and len(classes) and major in major_option_list and sex in ['男', '女'], '部分数据有误, 请重新填写'
                        classes = classes[0]
                        if len(grade[0]) == 2:
                            grade = '20' + grade[0]
                        else:
                            grade = grade[0]
                        student = Student(
                            stuId = float2str(stuUser['stuId']),
                            stuName=stuUser['stuName'],
                            major=major,
                            sex= sex,
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
                        # 系统角色默认为普通老师, 变动需在系统上更改
                        teacher = Teacher(
                            teaId = str(teaUser['teaId'])[:-2],
                            teaName = teaUser['teaName'],
                            teaSex = teaUser['teaSex'],
                            teaPosition = teaUser['teaPosition'],
                            teaEmail = teaUser['teaEmail'],
                            teaPhone = teaUser['teaPhone'][:-2],
                            roleId=1
                        )
                        db.session.add(teacher)
                # 最后提交并跳转到原本的地址
                db.session.commit()
                flash('导入成功')
                if from_url == "xJournal":
                    return redirect(url_for('.%s' % from_url, internId=internId))
                return redirect(url_for('.%s' % from_url))
            except Exception as e:
                #flash('导入出现异常:%'% str(e))
                if str(e) == '部分数据有误, 请重新填写':
                    flash('部分数据有误, 请重新填写')
                else:
                    flash('导入失败')
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
        files = request.files.getlist(x)
        try:
            for file in files:
                if file:
#           filename = secure_filename(file.filename)
                    dest = path_dict[x]
                    file_path = storage_cwd(internId, dest)
                    file.save(os.path.join(file_path, file.filename))
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
            #获取文件的pdf名称
            pdf_file = pdf_postfix(file)
            #获取原文件路径
            storage_path = os.path.join(storage_cwd(internId, dest), file)
            #获取对应pdf文件路径
            pdf_path = os.path.join(pdf_cwd(internId, dest), pdf_file)
            if os.path.exists(pdf_path):
                pdf_path = pdf_path[pdf_path.find('/static'):]
            else:
                os.system('unoconv -f pdf -o %s %s' % (pdf_path, storage_path))
                pdf_path = pdf_path[pdf_path.find('/static'):]
            return pdf_path
        elif file.split('.')[-1]=='pdf':
            pdf_file = file
            storage_path = os.path.join(storage_cwd(internId, dest), file)
            pdf_path = os.path.join(pdf_cwd(internId, dest), pdf_file)
            a=os.system('cp %s %s'%(storage_path,pdf_path))
            return pdf_path[pdf_path.find('/static'):]


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
                db.session.rollback()
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
                .add_columns(ComInfor.comName, InternshipInfor.comId, InternshipInfor.stuId, InternshipInfor.Id, InternshipInfor.start,
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
        pagination = intern.join(ComInfor, InternshipInfor.comId == ComInfor.comId)\
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
    internId = request.args.get('internId')
    #防sql注入
    if current_user.roleId == 0:
        stuId = current_user.stuId
        if stuId!=InternshipInfor.query.filter_by(Id=internId).first().stuId:
            flash('非法操作！')
            return redirect('/')
    else:
        stuId = request.args.get('stuId')
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
    #指导老师审核权限
    comfirm_can=is_schdirtea(stuId) or current_user.can(Permission.STU_JOUR_CHECK)
    if request.method == 'POST':
        return storage_download(internId)
    if current_user.roleId == 0:
        return render_template('xSum.html', Permission=Permission, comInfor=comInfor, internship=internship,
                               student=student, summary=summary, attachment=attachment, summary_doc=summary_doc,
                               path=path,comfirm_can=comfirm_can)
    elif internship.end < now:
        if internship.internCheck == 2:
            return render_template('xSum.html', Permission=Permission, comInfor=comInfor, internship=internship,
                                   student=student, summary=summary, attachment=attachment, summary_doc=summary_doc,
                                   path=path,comfirm_can=comfirm_can)
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
            for x in request.form:
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
                        if os.path.exists(pdf_path):
                            os.system('rm  %s'%pdf_path)
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
                        if os.path.exists(pdf_path):
                            os.rename(pdf_path, os.path.join(pdf_cwd(internId, dest_path), pdf_postfix(new_name)))
                        os.rename(storage_path, os.path.join(storage_cwd(internId, dest_path), new_name))
                        flash('重命名成功！')
            return redirect(url_for('.xSum_fileManager', stuId=stuId, internId=internId))

        return render_template('xSum_fileManager.html', Permission=Permission, comInfor=comInfor, internship=internship,
                               student=student, summary=summary, attachment=attachment, summary_doc=summary_doc)
    else:
        flash('该实习还没有结束,暂不能上传总结等文件！')
        return redirect(url_for('.xSum',stuId=stuId,internId=internId))


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
    if internship.internStatus != 2:
        flash('实习结束后方可提交成绩')
        return redirect(url_for('.xSum', internId=internId, stuId=stuId))
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
            if summary.comScore and summary.schScore:
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
    stuId = request.form.get('stuId')
    comfirm_can=is_schdirtea(stuId) or current_user.can(Permission.STU_SUM_SCO_CHECK)
    if comfirm_can:
        internId = request.form.get('internId')
        sumCheck = request.form.get('sumCheck')

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
    else:
        return redirect(url_for('.index'))


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
                     InternshipInfor.internCheck, InternshipInfor.task,
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
                db.session.rollback()
                flash('添加失败，请重试！')
                return redirect(url_for('.selectManage'))
    return render_template('selectManage.html',Permission=Permission,majors=majors,grades=grades,classess=classess)

#上传探访记录
@main.route('/teaVisit',methods=['GET','POST'])
@login_required
def teaVisit():
    permission = current_user.can(Permission.UPLOAD_VISIT)
    if not permission:
        flash('非法操作')
        return redirect('/')
    userId=current_user.get_id()
    page=request.args.get('page',1,type=int)
    #在线预览
    path=None
    filename=request.args.get('filename')
    if filename:
        path=os.path.join(STATIC_STORAGE,'visit',userId,filename)
    #end 在线阅览
    url='%s/visit/%s'%(STORAGE_FOLDER, userId)
    pagination=Visit.query.filter_by(userId=current_user.get_id()).order_by(Visit.time.desc()).paginate(page,per_page=3,error_out=False)
    visit=pagination.items
    if request.method=='POST':
        try:
            if 'delete' in request.form:
                filename=request.form.get('delete')
                os.remove(os.path.join(STORAGE_FOLDER,'visit',userId,filename))
                visit=Visit.query.filter_by(filename=filename,userId=userId).first()
                visitId=visit.visitId
                db.session.delete(visit)
                v_I=Visit_Intern.query.filter_by(visitId=visitId).all()
                if v_I:
                    for x in v_I:
                        os.remove(os.path.join(STORAGE_FOLDER,str(x.internId),'visit',userId,filename))
                        db.session.delete(x)
                    db.session.commit()
                flash('删除成功!')
                return redirect(url_for('.teaVisit'))
            if 'download' in request.form:
                #file_name=secure_filename(request.form.get('download'))
                file_name=request.form.get('download')
                return send_file(os.path.join(STORAGE_FOLDER,'visit',userId,file_name), as_attachment=True,
                             attachment_filename=file_name.encode('utf-8'))
        except Exception as e:
            db.session.rollback()
            flash('操作失败，请重试！')
            print('上传探访记录页面：',e)
            return redirect(url_for('.teaVisit'))
    return render_template('teaVisit.html',Permission=Permission,path=path,visit=visit,pagination=pagination,filename=filename)

#用于ajax异步获取某探访记录的相关学生表
@main.route('/studentTable/<uid>/<filename>',methods=['GET'])
@login_required
def student_table(uid,filename):
    visitId=Visit.query.filter_by(filename=filename,userId=uid).first().visitId
    show_infor=db.session.execute('select s.stuId,stuName,comName,start,end from Student as s,InternshipInfor as i,ComInfor as c,Visit_Intern as v where i.Id=v.internId and i.stuId=s.stuId and i.comId=c.comId and visitId=%s'%visitId)
    return render_template('studentTable.html',show_infor=show_infor)


#选择探访学生
@main.route('/selectStudent',methods=['GET','POST'])
@login_required
def selectStudent():
    grade={}
    major={}
    classes={}
    my={}
    page = request.args.get('page', 1, type=int)
    stu=create_stu_filter(grade, major, classes,my)
    if my.get(0):
        pagination=stu.join(ComInfor,ComInfor.comId==InternshipInfor.comId)\
    .add_columns(ComInfor.comName,Student.stuName,InternshipInfor.Id,Student.stuId,InternshipInfor.start,InternshipInfor.end).paginate(page, per_page=60, error_out=False)
    else:
        pagination=stu.join(InternshipInfor,InternshipInfor.stuId==Student.stuId).join(ComInfor,ComInfor.comId==InternshipInfor.comId)\
    .add_columns(ComInfor.comName,Student.stuName,InternshipInfor.Id,Student.stuId,InternshipInfor.start,InternshipInfor.end).paginate(page, per_page=60, error_out=False)
    internlist = pagination.items
    form=searchForm()
    userId=current_user.get_id()
    session['visit_students']=None
    if request.method=='POST':
        try:
            session['visit_students']=request.form.getlist('approve[]')
            flash('请上传本次探访记录！')
            return redirect(url_for('.upload_Visit'))
        except Exception as e:
            flash('操作失败，请重试！')
            print('上传探访记录时选择学生:',e)
            return redirect(url_for('.selectStudent'))
    return render_template('selectStudent.html',Permission=Permission,form=form,internlist=internlist,grade=grade,classes=classes,major=major,pagination=pagination)


#上传探访记录
@main.route('/upload_Visit',methods=['GET','POST'])
@login_required
def upload_Visit():
    permission = current_user.can(Permission.UPLOAD_VISIT)
    visitform=visitForm()
    if not permission:
        flash('非法操作')
        return redirect('/')
    userId=current_user.get_id()
    if request.method=='POST':
        visitId=None
        try:
            file=request.files.get('visit')
            if file:
                path='%s/visit/%s'%(STORAGE_FOLDER,userId)
                if not os.path.exists(path):
                    os.system('mkdir '+path)
                files=os.listdir(path)
                if file.filename in files:
                    flash("上传的探访记录有重名，请更换探访记录文件名称！")
                    return redirect(url_for(".upload_Visit"))
                tea_url='%s/visit/%s/%s'%(STORAGE_FOLDER,userId,file.filename)
                file.save(tea_url)
                visit=Visit(userId=userId,filename=file.filename,time=datetime.now(),vteaName=request.form.get('teaName'),visitTime=request.form.get('visitTime'),visitWay=request.form.get('visitWay'))
                db.session.add(visit)
                db.session.commit()
                visitId=getMaxVisitId()
                if session['visit_students']:
                    for x in session['visit_students']:
                        direction='%s/%s/visit/%s'%(STORAGE_FOLDER,x,userId)
                        if not os.path.exists(direction):
                            os.mkdir(direction)
                        shutil.copyfile(tea_url,os.path.join(direction,file.filename))
                        visit_intern=Visit_Intern(visitId=visitId,internId=x)
                        db.session.add(visit_intern)
                db.session.commit()
                flash('上传成功！')
                del(session['visit_students'])
                return redirect(url_for('.teaVisit'))
        except Exception as e:
            db.session.rollback()
            flash('操作失败，请重试！')
            visit=Visit.query.filter_by(visitId=visitId).first()
            if visit:
                db.session.delete(visit)
                db.session.commit()
            print('upload_Visit：',e)
            return redirect(url_for('.upload_Visit'))
    return render_template('upload_visit.html',Permission=Permission,visitform=visitform)



#学生的被探访记录
@main.route('/stuVisit',methods=['GET','POST'])
@login_required
def stuVisit():
    internId=request.args.get('internId')
    # session['internId']=internId
    #防止sql注入
    if current_user.roleId==0:
        stuId=InternshipInfor.query.filter_by(Id=internId).first().stuId
        if current_user.stuId!=stuId:
            flash('非法操作！')
            return redirect('/')
    url='%s/%s/visit/'%(STORAGE_FOLDER,internId)
    file=None
    file_path=[]
    fileId=None
    id_file=None
    teaName=None
    time=None
    #只考虑教师上传的探访记录
    visit_intern=Visit_Intern.query.filter_by(internId=internId).join(Visit,Visit.visitId==Visit_Intern.visitId).add_columns(Visit.vteaName,Visit.visitWay,Visit.visitTime,Visit.time,Teacher.teaName,Teacher.teaId,Visit.filename).join(Teacher,Teacher.teaId==Visit.userId).all()
    #在线阅读
    path=None
    filename=request.args.get('filename')
    fileid=request.args.get('fileId')
    if filename and fileid:
        path='%s/%s/visit/%s/%s'%(STATIC_STORAGE,internId,fileid,filename)
    #在线阅读end
    if request.method=='POST':
        try:
            if 'delete' in request.form:
                userId=request.form.get('fileId')
                filename=request.form.get('delete')
                os.remove(os.path.join(url,userId,filename))
                visitId=Visit.query.filter_by(userId=userId,filename=filename).first().visitId
                v_i=Visit_Intern.query.filter_by(visitId=visitId,internId=internId).first()
                db.session.delete(v_i)
                db.session.commit()
                flash('删除成功！')
                # del(session['internId'])
                return redirect(url_for('.stuVisit',internId=internId))
            if 'download' in request.form:
                file_name=request.form.get('download')
                return send_file(os.path.join(url,request.form.get('fileId'),file_name), as_attachment=True,
                             attachment_filename=file_name.encode('utf-8'))
            flash('操作成功！')
            return redirect(url_for('.stuVisit',internId=internId))
        except Exception as e:
            db.session.rollback()
            flash('操作失败！请重试！')
            return redirect(url_for('.stuVisit',internId=internId))
    return render_template('stuVisit.html',Permission=Permission,path=path,visit_intern=visit_intern,internId=internId)

#学生的被探访记录
@main.route('/allTeaVisit',methods=['GET','POST'])
@login_required
def allTeaVisit():
    permission = current_user.can(Permission.UPLOAD_VISIT)
    if not permission:
        flash('非法操作')
        return redirect('/')
    uid=request.args.get('uid')
    page=request.args.get('page',1,type=int)
    #在线预览
    path=None
    filename=request.args.get('filename')
    if filename:
        path=os.path.join(STATIC_STORAGE,'visit',uid,filename)
    #end 在线阅览
    #url='%s/visit/%s'%(STORAGE_FOLDER, userId)
    pagination=Visit.query.order_by(Visit.time.desc()).join(Teacher,Teacher.teaId==Visit.userId).add_columns(Visit.userId,Visit.vteaName,Visit.visitWay,Visit.visitTime,Visit.time,Teacher.teaName,Teacher.teaId,Visit.filename).paginate(page,per_page=6,error_out=False)
    visit=pagination.items

    if request.args.get('export_all'):
        # transform the folder's name from English to Chinese
        def visit_tar_transform():
            teacher = Teacher.query.all()
            transform = ["--transform='s,%s,%s,'" % (tea.teaId,tea.teaName) for tea in teacher]
            transform.append("--transform='s,visit,探访记录汇总,'")
            transform = " ".join(transform)
            return transform
        transform = visit_tar_transform()
        zip_file = os.path.join(VISIT_EXPORT_ALL_FOLDER,str(time.time()) + ".zip")
        visit_folder = os.path.join(STORAGE_FOLDER,'visit')
        os.system("tar --transform='s,^.*storage/,,' %s -cf %s %s" % (transform, zip_file, visit_folder))
        file_attachname = "探访记录汇总_%s.zip" % datetime.now().date()
        return send_file(zip_file, as_attachment=True, attachment_filename=file_attachname.encode('utf-8'))

    if request.method=='POST':
        try:
            if 'download' in request.form:
                #file_name=secure_filename(request.form.get('download'))
                file_name=request.form.get('download')
                userId=request.form.get('userId')
                return send_file(os.path.join(STORAGE_FOLDER,'visit',userId,file_name), as_attachment=True,
                             attachment_filename=file_name.encode('utf-8'))


        except Exception as e:
            flash('操作失败，请重试！')
            print('allTeaVisit：',e)
            return redirect(url_for('.allTeaVisit'))
    return render_template('allTeaVisit.html',Permission=Permission,path=path,visit=visit,pagination=pagination)

@main.route('/editIntroduce',methods=['GET','POST'])
@login_required
def editIntroduce():
    introduceform=introduceForm()
    if request.method=="POST":
        try:
            introduce=Introduce(content=request.form.get('content'),time=datetime.now().date())
            db.session.add(introduce)
            db.session.commit()
            flash('修改成功！')
        except Exception as e:
            db.session.rollback()
            flash('修改失败！')
            print('首页介绍修改：',e)
        return redirect(url_for('.index'))
    return render_template('editIntroduce.html',Permission=Permission,introduceform=introduceform)

#返回主页介绍修改前的json
@main.route('/getIntroduce_json',methods=['GET'])
@login_required
def getIntroduce_json():
    content=db.session.execute('select content from Introduce where Id=(select max(Id) from Introduce)')
    content_value={}
    for x in content:
        content_value['content']=x[0]
    content_json=json.dumps(content_value)
    return content_json

@main.route('/improveTeaInfor',methods=['GET'])
@login_required
def improveTeaInfor():
    if not (current_user.teaEmail and current_user.teaPhone):
        flash('请先完善相关信息！')
    return redirect(url_for('.editTeacher',teaId=current_user.get_id()))
