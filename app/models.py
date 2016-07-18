from . import db
from flask.ext.login import UserMixin
from . import login_manager
from datetime import datetime


@login_manager.user_loader
def load_user(Id):
    return Teacher.query.get(Id) or Student.query.get(Id)


class Role(db.Model):
    __tablename__ = 'Role'
    roleId = db.Column(db.Integer, primary_key=True)
    roleName = db.Column(db.String(5), unique=True)
    permission = db.Column(db.String(8), unique=True)
    # backref='role'可代替Teacher的roleId
    teacher = db.relationship('Teacher', backref='role', lazy='dynamic')
    student = db.relationship('Student', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class Teacher(db.Model, UserMixin):
    __tablename__ = 'Teacher'
    teaId = db.Column(db.String(10), primary_key=True)
    teaName = db.Column(db.String(4), index=True)
    roleId = db.Column(db.Integer, db.ForeignKey('Role.roleId'))
    password = db.Column(db.String(10))

    def get_id(self):
        return self.teaId

    # 对教师用户进行权限判断
    def can(self, permissions):
        if self.role.permission is not None:
            p = eval(self.role.permission)
        return (p & permissions) == permissions

    def __repr__(self):
        return '<Teacher %r>' % self.teaName


class Student(db.Model, UserMixin):
    __tablename__ = 'Student'
    stuId = db.Column(db.String(20), primary_key=True)
    stuName = db.Column(db.String(10), index=True)
    institutes = db.Column(db.String(10))
    major = db.Column(db.String(10))
    grade = db.Column(db.String(10))
    sex = db.Column(db.String(2))
    classes = db.Column(db.String(10))
    inforStatus = db.Column(db.Integer)
    jourStatus = db.Column(db.Integer)
    sumStatus = db.Column(db.Integer)
    roleId = db.Column(db.Integer, db.ForeignKey('Role.roleId'))
    password = db.Column(db.String(10))

    def get_id(self):
        return self.stuId

    # 对学生用户进行权限判断
    def can(self, permissions):
        if self.role.permission is not None:
            p = eval(self.role.permission)
        return (p & permissions) == permissions

    def __repr__(self):
        return '<Student %r>' % self.stuName


class ComInfor(db.Model):
    __tablename__ = 'ComInfor'
    comId = db.Column(db.Integer, primary_key=True)
    comName = db.Column(db.String(20))
    comBrief = db.Column(db.String(200))
    comAddress = db.Column(db.String(100))
    comUrl = db.Column(db.String(50))
    comMon = db.Column(db.String(10))
    comProject = db.Column(db.String(100))
    comStaff = db.Column(db.Integer)
    comContact = db.Column(db.String(10))
    comPhone = db.Column(db.String(20))
    comEmail = db.Column(db.String(20))
    comFax = db.Column(db.String(20))
    comDate = db.Column(db.DATETIME, default=datetime.utcnow)
    status = db.Column(db.Integer, default=0)
    student = db.relationship('InternshipInfor', backref='cominfor', lazy='dynamic')

    # 创建大量虚拟信息
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py

        seed()
        for i in range(count):
            comInfor = ComInfor(comName=forgery_py.internet.user_name(True),
                                comBrief=forgery_py.lorem_ipsum.sentences(),
                                comAddress=forgery_py.address.city(), comUrl=forgery_py.internet.domain_name(),
                                comMon=randint(100, 10000), comProject=forgery_py.lorem_ipsum.word(),
                                comStaff=randint(100, 10000),
                                comContact=forgery_py.name.full_name(), comPhone=forgery_py.address.phone(),
                                comEmail=forgery_py.internet.email_address(user=None),
                                comFax=forgery_py.address.phone(),
                                status=randint(0, 3))
            db.session.add(comInfor)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class InternshipInfor(db.Model):
    __tablename__ = 'InternshipInfor'
    Id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200))
    address = db.Column(db.String(200))
    opinion = db.Column(db.String(250))
    start = db.Column(db.Date)
    end = db.Column(db.Date)
    time = db.Column(db.DATETIME, default=datetime.utcnow())
    teaId = db.Column(db.String(8))
    status = db.Column(db.Integer, default=0)
    statusTime = db.Column(db.DATETIME)
    comId = db.Column(db.Integer, db.ForeignKey('ComInfor.comId'))
    stuId = db.Column(db.String(20), db.ForeignKey('Student.stuId'))


class DirctTea(db.Model):
    __tablename__ = 'DirctTea'
    Id = db.Column(db.Integer, primary_key=True)
    teaId = db.Column(db.String(10))
    teaName = db.Column(db.String(10))
    teaDuty = db.Column(db.String(20))
    teaPhone = db.Column(db.String(15))
    teaEmail = db.Column(db.String(20))
    cteaName = db.Column(db.String(10))
    cteaDuty = db.Column(db.String(20))
    cteaPhone = db.Column(db.String(15))
    cteaEmail = db.Column(db.String(20))
    stuId = db.Column(db.String(20), db.ForeignKey('Student.stuId'))


class Permission:
    # 企业信息查询
    COM_INFOR_SEARCH = 0X0000001
    # 企业信息编辑
    COM_INFOR_EDIT = 0X0000002
    # 企业信息审核
    COM_INFOR_CHECK = 0X0000004

    # 实习企业信息列表
    INTERNSHIP_LIST = 0X0000008
    # 学生实习信息列表
    STU_INFOR_LIST = 0X0000010

    # 学生实习信息查看
    STU_INFOR_SEARCH = 0X0000020
    # 学生实习信息编辑
    STU_INFOR_EDIT = 0X0000040
    # 学生实习信息审核
    STU_INFOR_CHECK = 0X0000080
    # 学生实习信息导出
    STU_INFOR_EXPORT = 0X0000100

    # 学生实习日志查询
    STU_JOUR_SEARCH = 0X0000200
    # 学生实习日志编辑
    STU_JOUR_EDIT = 0X0000400
    # 学生实习日志审核
    STU_JOUR_CHECK = 0X0000800
    # 学生实习日志导出
    STU_JOUR_EXPORT = 0X0001000

    # 学生实习总结查看
    STU_SUM_SEARCH = 0X0002000
    # 学生实习总结编辑
    STU_SUM_EDIT = 0X0004000
    # 学生实习总结导出
    STU_SUM_EXPORT = 0X0008000
    # 学生实习总结审核
    STU_SUM_CHECK = 0X0010000

    # 学生实习成绩查看
    STU_SCO_SEARCH = 0X0020000
    # 学生实习成绩编辑
    STU_SCO_EDIT = 0X0040000
    # 学生实习成绩导出
    STU_SCO_EXPORT = 0X0080000

    # 管理
    ADMIN = 0X0100000
    # 学生信息导入
    STU_INFOR_IMPORT = 0X0200000
    # 老师信息导入
    TEA_INFOR_IMPORT = 0X0400000
    # 权限管理
    PERMIS_MANAGE = 0X0800000
    # # 下拉框管理,改为自动生成
    # LIST_MANAGE = 0X1000000
