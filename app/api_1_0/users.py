from . import api
from flask import jsonify,request
from ..models import Teacher,Student

@api.route('/teachers/<key>')
def teachers(key):
    '''key 用在before_request中'''
    tea={}
    teacher=Teacher.query.filter(Teacher.teaId!='20149062').all()
    for item in teacher:
        tea[item.teaId]={'name':item.teaName,'sex':item.teaSex,'position':item.teaPosition,'email':item.teaEmail,'phone':item.teaPhone}
    return jsonify(tea)

@api.route('/students/<key>')
def students(key):
    '''key 用在before_request中'''
    tea={}
    major=request.args.get('major')
    grade=request.args.get('grade')
    classes=request.args.get('class')
    student=Student.query
    if major:
        student=student.filter_by(major=major)
    if grade:
        student=student.filter_by(grade=grade)
    if classes:
        student=student.filter_by(classes=classes)
    student=student.all()
    stu={}
    for item in student:
        stu[item.stuId]={'name':item.stuName,'sex':item.sex,'major':item.major,'grade':item.grade,'class':item.classes}
    return jsonify(stu)
