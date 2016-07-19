from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, DateTimeField
from wtforms.validators import Required, URL, Email

class searchform(Form):
    key = StringField(validators=[Required(message='请先输入搜索内容')])
    submit = SubmitField('搜索')


class comform(Form):
    comName = StringField('公司名称', validators=[Required(message='此项不能为空')])
    comAdress = StringField('公司地址', validators=[Required(message='此项不能为空')])
    comUrl = StringField('公司网址', validators=[Required(message='此项不能为空'), URL(message='请输入正确的URL')])
    comBrief = TextAreaField('公司简介')
    comProject = TextAreaField('营业项目', validators=[Required(message='此项不能为空')])
    comMon = StringField('营业额', validators=[Required(message='此项不能为空')])
    comStaff = StringField('员工人数', validators=[Required(message='此项不能为空')])
    comContact = StringField('联系人', validators=[Required(message='此项不能为空')])
    comPhone = StringField('联系电话', validators=[Required(message='此项不能为空')])
    comEmail = StringField('Email', validators=[Required(message='此项不能为空'), Email(message='请输入正确的邮箱地址')])
    comFax = StringField('传真', validators=[Required(message='此项不能为空')])
    submit = SubmitField('下一步')


class internshipForm(Form):
    task = TextAreaField('实习任务', validators=[Required(message='此项不能为空')])
    adress = StringField('实习地址', validators=[Required(message='此项不能为空')])
    start = DateTimeField('开始时间', format='%Y-%m-%d', validators=[Required()])
    end = DateTimeField('结束时间', format='%Y-%m-%d', validators=[Required(message='请按 年-月-日 的格式输入正确的日期')])
    submit = SubmitField('提交')


class dirctTeaForm(Form):
    teaId = StringField('教师工号')
    teaName = StringField('姓名')
    teaDuty = StringField('职称')
    teaPhone = StringField('联系电话')
    teaEmail = StringField('邮箱')
    cteaName = StringField('姓名')
    cteaDuty = StringField('职称')
    cteaPhone = StringField('联系电话')
    cteaEmail = StringField('邮箱')


class journalForm(Form):
    workStart = StringField('开始日期', validators=[Required()])
    weekNo = StringField('周数', validators=[Required()])
    mon = TextAreaField('周一', validators=[Required()])
    tue = TextAreaField('周二', validators=[Required()])
    wed = TextAreaField('周三', validators=[Required()])
    thu = TextAreaField('周四', validators=[Required()])
    fri = TextAreaField('周五', validators=[Required()])
    submit=SubmitField('提交')
