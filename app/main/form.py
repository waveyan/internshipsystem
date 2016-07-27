from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, DateTimeField, SelectField, BooleanField, DateField, validators
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
    # workStart = DateField('开始日期', validators=[Required(message='此项不能为空')])
    workStart = DateField('开始日期', format="%Y-%m-%d")
    weekNo = StringField('周数', validators=[Required(message='此项不能为空')])
    mon = TextAreaField('周一', validators=[Required(message='此项不能为空')])
    tue = TextAreaField('周二', validators=[Required(message='此项不能为空')])
    wed = TextAreaField('周三', validators=[Required(message='此项不能为空')])
    thu = TextAreaField('周四', validators=[Required(message='此项不能为空')])
    fri = TextAreaField('周五', validators=[Required(message='此项不能为空')])
    submit = SubmitField('提交')


class stuForm(Form):
    stuId = StringField('学号', validators=[Required(message='此项不能为空')])
    stuName = StringField('姓名', validators=[Required(message='此项不能为空')])
    sex = SelectField('性别', choices=[('男', '男'), ('女', '女')], default='女')
    institutes = StringField('学院', validators=[Required(message='此项不能为空')])
    grade = StringField('年级', validators=[Required(message='此项不能为空')])
    major = StringField('专业', validators=[Required(message='此项不能为空')])
    classes = StringField('班级', validators=[Required(message='此项不能为空')])
    submit = SubmitField('提交')


class teaForm(Form):
    teaId = StringField('教工号', validators=[Required(message='此项不能为空')])
    teaName = StringField('姓名', validators=[Required(message='此项不能为空')])
    teaSex = SelectField('性别', choices=[('男', '男'), ('女', '女')], default='女')
    submit = SubmitField('提交')


class permissionForm(Form):
    roleName = StringField('角色名称', validators=[Required(message='此项不能为空')])
    COM_INFOR_SEARCH = BooleanField('企业信息查看', default=False, description='0X0000001', false_values='0x11')
    COM_INFOR_EDIT = BooleanField('企业信息编辑', default=False, description='0X0000002')
    COM_INFOR_CHECK = BooleanField('企业信息审核', default=False, description='0X0000004')
    INTERNSHIP_LIST = BooleanField('实习企业信息列表', default=False, description='0X0000008')
    STU_INFOR_LIST = BooleanField('学生实习信息列表', default=False, description='0X0000010')
    STU_INFOR_SEARCH = BooleanField('学生实习信息查看', default=False, description='0X0000020')
    STU_INFOR_EDIT = BooleanField('学生实习信息编辑', default=False, description='0X0000040')
    STU_INFOR_CHECK = BooleanField('学生实习信息审核', default=False, description='0X0000080')
    STU_INFOR_EXPORT = BooleanField('学生实习信息导出', default=False, description='0X0000100')
    STU_JOUR_SEARCH = BooleanField('学生实习日志查询', default=False, description='0X0000200')
    STU_JOUR_EDIT = BooleanField('学生实习日志编辑', default=False, description='0X0000400')
    STU_JOUR_CHECK = BooleanField('学生实习日志审核', default=False, description='0X0000800')
    STU_JOUR_EXPORT = BooleanField('学生实习日志导出', default=False, description='0X0001000')
    STU_SUM_SEARCH = BooleanField('学生实习总结查看', default=False, description='0X0002000')
    STU_SUM_EDIT = BooleanField('学生实习总结编辑', default=False, description='0X0004000')
    STU_SUM_EXPORT = BooleanField('学生实习总结导出', default=False, description='0X0008000')
    STU_SUM_CHECK = BooleanField('学生实习总结审核', default=False, description='0X0010000')
    STU_SCO_SEARCH = BooleanField('学生实习成果查看', default=False, description='0X0020000')
    STU_SCO_EDIT = BooleanField('学生实习成果编辑', default=False, description='0X0040000')
    STU_SCO_EXPORT = BooleanField('学生实习成果导出', default=False, description='0X0080000')
    ADMIN = BooleanField('管理', default=False, description='0x0100000')
    STU_INFOR_IMPORT = BooleanField('学生信息导入', default=False, description='0X0200000')
    TEA_INFOR_IMPORT = BooleanField('老师信息导入', default=False, description='0X0400000')
    PERMIS_MANAGE = BooleanField('权限管理', default=False, description='0X0800000')
    submit = SubmitField('提交')
