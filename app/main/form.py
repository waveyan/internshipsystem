from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, DateTimeField, SelectField, BooleanField, DateField, \
    validators, FileField
from wtforms.validators import Required, URL, Email

# datepicker failed
'''
from wtforms import widgets
class ExampleForm(Form):
    dt = DateField('DatePicker', format='%Y-%m-%d')
    submit = SubmitField('提交')


class DatePickerWidget(widgets.TextInput):
    """
        Date picker widget.

        You must include bootstrap-datepicker.js and form.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'datepicker'
        return super(DatePickerWidget, self).__call__(field, **kwargs)
'''


class searchForm(Form):
    key = StringField(validators=[Required(message='请先输入搜索内容')])
    submit = SubmitField('搜索')


class comForm(Form):
    comName = StringField('公司名称', validators=[Required(message='此项不能为空')], id='task')
    comAddress = StringField('公司地址', validators=[Required(message='此项不能为空')])
    comUrl = StringField('公司网址', validators=[Required(message='此项不能为空'), URL(message='请输入正确的URL')])
    comBrief = TextAreaField('公司简介')
    comProject = TextAreaField('营业项目', validators=[Required(message='此项不能为空')])
    comMon = StringField('营业额', validators=[Required(message='此项不能为空')])
    comStaff = StringField('员工人数', validators=[Required(message='此项不能为空')])
    comContact = StringField('联系人', validators=[Required(message='此项不能为空')])
    comPhone = StringField('联系电话', validators=[Required(message='此项不能为空')])
    comEmail = StringField('Email', validators=[Required(message='此项不能为空'), Email(message='请输入正确的邮箱地址')])
    comFax = StringField('传真', validators=[Required(message='此项不能为空')])
    submit = SubmitField('提交')


class internshipForm(Form):
    task = TextAreaField('实习任务', validators=[Required(message='此项不能为空')])
    address = StringField('实习地址', validators=[Required(message='此项不能为空')])
    start = DateTimeField('开始时间', format='%Y-%m-%d', validators=[Required()])
    end = DateTimeField('结束时间', format='%Y-%m-%d', validators=[Required(message='请按 年-月-日 的格式输入正确的日期')])
    submit = SubmitField('提交')


'''
# delete
class directTeaForm(Form):
    teaId = StringField('教师工号')
    teaName = StringField('姓名')
    teaDuty = StringField('职称')
    teaPhone = StringField('联系电话')
    teaEmail = StringField('邮箱')
    cteaName = StringField('姓名')
    cteaDuty = StringField('职称')
    cteaPhone = StringField('联系电话')
    cteaEmail = StringField('邮箱')
'''


class schdirteaForm(Form):
    steaId = StringField('校内教师工号')
    steaName = StringField('姓名')
    steaDuty = StringField('职称')
    steaPhone = StringField('联系电话')
    steaEmail = StringField('邮箱')


class comdirteaForm(Form):
    cteaName = StringField('企业教师姓名')
    cteaDuty = StringField('职称')
    cteaPhone = StringField('联系电话')
    cteaEmail = StringField('邮箱')
    submit = SubmitField('提交')


class journalForm(Form):
    workStart = DateField('开始日期', format="%Y-%m-%d", validators=[Required(message='此项不能为空')])
    weekNo = StringField('周数', validators=[Required(message='此项不能为空')])
    mon = TextAreaField('周一', id='mon')
    tue = TextAreaField('周二', id='tue')
    wed = TextAreaField('周三', id='wed')
    thu = TextAreaField('周四', id='thu')
    fri = TextAreaField('周五', id='fri')
    sat = TextAreaField('周六', id='sat')
    sun = TextAreaField('周日', id='sun')
    submit = SubmitField('提交')


class stuForm(Form):
    stuId = StringField('学号', validators=[Required(message='此项不能为空')])
    stuName = StringField('姓名', validators=[Required(message='此项不能为空')])
    sex = SelectField('性别', choices=[('男', '男'), ('女', '女')], default='男')
    institutes = StringField('学院', default='计算机学院', validators=[Required(message='此项不能为空')])
    grade = StringField('年级', validators=[Required(message='此项不能为空')])
    major = StringField('专业', validators=[Required(message='此项不能为空')])
    classes = StringField('班级', validators=[Required(message='此项不能为空')])
    submit = SubmitField('提交')


class teaForm(Form):
    teaId = StringField('教工号', validators=[Required(message='此项不能为空')])
    teaName = StringField('姓名', validators=[Required(message='此项不能为空')])
    teaSex = SelectField('性别', choices=[('男', '男'), ('女', '女')], default='男')
    submit = SubmitField('提交')


class permissionForm(Form):
    roleName = StringField('角色名称', validators=[Required(message='此项不能为空')])
    roleDescribe = TextAreaField('角色描述')
    COM_INFOR_SEARCH = BooleanField('企业信息查看', default=False, description='0X0000009', false_values='0x11')
    COM_INFOR_EDIT = BooleanField('企业信息编辑', default=False, description='0X000000B')
    COM_INFOR_CHECK = BooleanField('企业信息审核', default=False, description='0X000000F')
    INTERNCOMPANY_LIST = BooleanField('实习企业信息列表', default=False, description='0X0000008')
    STU_INTERN_LIST = BooleanField('学生实习信息列表', default=False, description='0X0000010')
    STU_INTERN_SEARCH = BooleanField('学生实习信息查看', default=False, description='0X0000030')
    STU_INTERN_EDIT = BooleanField('学生实习信息编辑', default=False, description='0X0000070')
    STU_INTERN_CHECK = BooleanField('学生实习信息审核', default=False, description='0X00000F0')
    STU_JOUR_SEARCH = BooleanField('学生实习日志查看', default=False, description='0X0000210')
    STU_JOUR_EDIT = BooleanField('学生实习日志编辑', default=False, description='0X0000610')
    STU_JOUR_CHECK = BooleanField('学生实习日志审核', default=False, description='0X0000E10')
    STU_SUM_SEARCH = BooleanField('学生实习总结与成果查看', default=False, description='0X0001010')
    STU_SUM_EDIT = BooleanField('学生实习总结与成果编辑', default=False, description='0X0003010')
    STU_SUM_SCO_CHECK = BooleanField('学生实习总结和成果审核', default=False, description='0X0007010')
    STU_INTERN_MANAGE = BooleanField('学生信息管理', default=False, description='0X0010000')
    TEA_INFOR_MANAGE = BooleanField('老师信息管理', default=False, description='0X0020000')
    PERMIS_MANAGE = BooleanField('权限管理', default=False, description='0X0040000')
    submit = SubmitField('提交')


class xSumScoreForm(Form):
    comScore = StringField('企业实习评分', validators=[Required(message='此项不能为空')])
    schScore = StringField('校内指导老师评分', validators=[Required(message='此项不能为空')])
    comfile = FileField('企业实习评分表')
    schfile = FileField('校内评分表')
    submit = SubmitField('保存')
