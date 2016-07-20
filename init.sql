
-- 年级表（Grade）
create table Grade (
grade varchar(8) NOT NULL PRIMARY KEY comment "年级"
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- 专业表（Major）
create table Major (
grade varchar(8) NOT NULL comment "年级",
major varchar(15) NOT NULL comment "专业",
PRIMARY KEY (grade,major),
KEY gradeFK(grade),
CONSTRAINT gradeFK FOREIGN KEY (grade)REFERENCES Grade(grade)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- 班级表(class)
create table Class (
class varchar(5) NOT NULL comment "班级",
major VARCHAR(10) NULL comment "专业",
grade VARCHAR (8)NOT NULL comment'年级',
PRIMARY KEY (class,major,grade),
KEY majorFK(majorId),
CONSTRAINT majorFK FOREIGN KEY (major) REFERENCES Major(major)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

--角色表(Role)
create TABLE Role(
roleId INT(3) NOT NULL ,
roleName VARCHAR (20) NOT NULL ,
roleDescribe VARCHAR (50) NOT NULL ,
permission VARCHAR (15) NOT NULL,
PRIMARY KEY (roleId)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

--教师表(Teacher)
create TABLE Teacher(
teaId varchar(10) NOT NULL comment'教师ID',
teaName VARCHAR (10) NOT  NULL ,
roleId INT(3)  NOT NULL ,
password VARCHAR (10) NOT NULL,
PRIMARY KEY (teaId),
KEY roleFK(roleId),
CONSTRAINT roleFK FOREIGN KEY (roleId) REFERENCES Role (roleId)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- 学生信息表（Student）
create table Student (
stuId varchar(20) not null primary key ,
stuName varchar(4) NOT NULL comment "姓名",
institutes varchar(10) NOT NULL comment "学院",
major varchar(10) NOT NULL comment "专业",
grade varchar(5) NOT NULL comment "年级",
classes varchar(2) NOT NULL comment "班级",
sex VARCHAR (2) NOT NULL comment'性别',
password VARCHAR (10) NOT NULL,
inforStatus int DEFAULT 0 NOT NULL comment "实习信息审核提示（0无提示，1提示）",
jourStatus int DEFAULT 0 NOT NULL comment "实习日志审核提示（0无提示，1提示）",
sumStatus int DEFAULT 0 NOT  NULL comment "实习总结审核提示（0无提示，1提示）",
roleId int DEFAULT 0 NOT NULL comment "角色ID，外键对应Role表的roleId"
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- 企业信息表（ComInfor）
create table ComInfor (
comId INT(20) not null primary key AUTO_INCREMENT comment "企业号",
comName varchar(20) NOT NULL comment "企业名称",
comBrief varchar(200) NOT NULL comment "企业简介",
comAddress VARCHAR (100) NOT NULL comment'企业地址',
comUrl VARCHAR (50)NOT NULL comment'企业网址',
comMon VARCHAR (10)NOT NULL comment'企业营业额',
comContact VARCHAR (10)NOT NULL comment'企业联系人',
comDate DATE NOT NULL comment'录入信息时间',
comProject varchar(100) NOT NULL comment "企业项目",
comStaff INT(10) NOT NULL comment "员工人数",
comPhone varchar(20) NOT NULL comment "联系电话",
comEmail varchar(20) comment "公司邮箱",
comFax varchar(20) NOT NULL comment "公司传真",
students INT (20) NOT  NULL commint'累计实习人数',
Status int DEFAULT 0 NULL comment "审核状态（0表示待审核，2表示被退回修改，3表示审核通过）"
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- 学生实习信息表（InternshipInfor）
create table InternshipInfor (
Id int(20) not null primary key AUTO_INCREMENT,
task varchar(200) NOT NULL comment "实习任务",
address VARCHAR (200) NOT NULL comment'实习地点',
start date NOT NULL comment "实习开始时间",
end date NOT NULL comment "实习结束时间",
time DATE NOT NULL comment'录入时间',
internStatus INT NOT NULL comment'实习状态(0实习中，1,实习结束)',
teaId varchar(8) NULL comment "审核教师工号",
opinion VARCHAR (250) NULL comment'审核意见',
status int DEFAULT 0  NULL comment "审核状态（0表示待审核，2表示被退回修改，3表示审核通过）",
statusTime datetime  NULL comment "审核时间",
comId INT(20) NOT NULL comment "对应ComInfor表的comId",
stuId varchar(20) NOT NULL comment "对应Student表的stuId",
KEY stuFK(stuId),
KEY comFK(comId),
CONSTRAINT stuFK FOREIGN KEY (stuId)REFERENCES Student(stuId),
CONSTRAINT comFK FOREIGN KEY (comId)REFERENCES ComInfor(comId)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- 指导老师信息表（DirctTea）
create table DirctTea(
Id int(10) primary key AUTO_INCREMENT,
teaId varchar(10) NOT NULL comment'教师ID',
teaName varchar(10)  NULL comment "校内指导老师姓名",
teaDuty varchar(20)  NULL comment "校内指导老师职务",
teaPhone varchar(15)  NULL comment "校内指导老师电话",
teaEmail varchar(20)  NULL comment "校内指导老师Email",
cteaName varchar(10)  NULL comment "企业指导老师姓名",
cteaDuty varchar(20)  NULL comment "企业指导老师职务",
cteaPhone varchar(15)  NULL comment "企业指导老师电话",
cteaEmail varchar(20)  NULL comment "企业指导老师Email",
comId INT (20) NOT NULL ,
stuId varchar(12) NOT NULL comment "对应Student表的stuId",
KEY dircTeaFK1(stuId),
KEY dirTeaFk2(comId),
CONSTRAINT dircTeaFK1 FOREIGN KEY (stuId)REFERENCES Student(stuId),
CONSTRAINT dirctTeaFK2 FOREIGN KEY (comId)REFERENCES ComInfor(comId)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- 实习工作总结表（Summary）
create table Summary(
sumId INT (20) NOT NULL AUTO_INCREMENT,
stuId varchar(15) NOT NULL comment "对应Student表",
purpose varchar(250) NOT NULL comment "实习目的",
process varchar(500) NOT NULL comment "实习过程",
summary varchar(500) NOT NULL comment "实习总结或体会",
status int DEFAULT 0 NULL comment "审核状态（0表示待审核，2表示被退回修改，3表示审核通过）",
traId varchar(8) NULL comment "审核教师工号",
time datetime NULL comment "审核时间",
KEY sumFK(stuId),
PRIMARY KEY (sumId),
CONSTRAINT sumFK FOREIGN KEY (stuId)REFERENCES Student(stuId)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- 实习日志表（Journal）
create table Journal (
Id INT (20)NOT  NULL PRIMARY KEY AUTO_INCREMENT,
stuId varchar(20) not null comment "学号,对应Student表",
comId INT (20) NOT NULL ,
weekNo int NOT NULL comment "实习周数",
workStart date NOT NULL comment "开始时间",
workEnd DATE NOT NULL comment'结束时间',
mon varchar(500) NOT NULL comment "周一实习内容",
tue varchar(500) NOT NULL comment "周二实习内容",
wed varchar(500) NOT NULL comment "周三实习内容",
thu varchar(500) NOT NULL comment "周四实习内容",
fri varchar(500) NOT NULL comment "周五实习内容",
status int DEFAULT 0 NULL comment "审核状态（0表示待审核，2表示被退回修改，3表示审核通过）",
teaId varchar(8) NULL comment "审核教师工号",
time datetime NULL comment "审核时间",
KEY jourFK1(stuId),
KEY jourFK2(comId),
CONSTRAINT jourFK1 FOREIGN KEY (stuId)REFERENCES Student(stuId),
CONSTRAINT jourFK2 FOREIGN KEY (comId)REFERENCES ComInfor(comId)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


INSERT INTO Role(roleId,roleName,roleDescribe,permission)values
(0,'student','student','0x0000009'),
(1,'teacher','teacher','0x00AB33F'),
(2,'checkTeacher','checkTeacher','0x00FFFFF'),
(3,'admin','admin','0xFFFFFFF');

insert into Teacher (teaId, teaName, roleId, password) values
('11111111','l',3,'11111111'),
('1111111','y',2,'1111111'),
('111111','w',1,'111111');

insert into Student (stuId, stuName, institutes, major, grade,sex, classes, password)
values ('201441402213','严伟力','计算机学院','计算机科学与技术','2014级','男','2班','123456');

