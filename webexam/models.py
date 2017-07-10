#!/usr/bin/env python
#-*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from webexam.database import Base
from flask.ext.login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
import json
from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin,Base):
    '''定义用户，用于认证和练习跟踪，密码进行哈希存储
    '''

    __tablename__ = 'user'
    id = Column(Integer,primary_key=True)
    username = Column(String(50), unique=True)
    password_hash = Column(String(128))
    department = Column(String(50))
    role = Column(String(50))
    sortorder = Column(Integer)

    def __init__(self, username=None, department=None, role=None, sortorder=100):
        self.username = username
        self.department = department
        self.role = role
        self.sortorder = sortorder

    def json(self):
        json_obj = {'id': self.id, 'username': self.username,'password':'',
                    'department': self.department, 'role': self.role, 'sortorder': self.sortorder}
        return json.dumps(json_obj)

    def from_json(self, data):
        self.username = data['username']
        if data['password'] != '':
            self.password = data['password']
        self.department = data['department']
        self.role = data['role']
        self.sortorder = data['sortorder']

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

class Lib(Base):
    '''定义题库名称表
    '''

    __tablename__ = 'lib'
    id = Column(Integer, primary_key=True)
    libname = Column(String(50), unique=True)
    sortorder = Column(Integer)

    def __init__(self, libname=None, sortorder=100):
        self.libname = libname
        self.sortorder = sortorder

    def json(self):
        json_obj = {'id': self.id, 'libname': self.libname,
                    'sortorder': self.sortorder}
        return json.dumps(json_obj)

    def from_json(self, data):
        self.libname = data['libname']
        self.sortorder = data['sortorder']


class Section(Base):
    '''定义题库的章节
    '''

    __tablename__ = 'section'
    id = Column(Integer, primary_key=True)
    libid = Column(Integer, ForeignKey('lib.id'))
    sectionname = Column(String(50), nullable=False)
    sortorder = Column(Integer)

    lib = relationship('Lib')

    def __init__(self, libid=None, sectionname=None, sortorder=100):
        self.libid = libid
        self.sectionname = sectionname
        self.sortorder = sortorder

    def json(self):
        json_obj = {'id': self.id, 'libid': self.libid, 'libname': self.lib.libname,
                    'sectionname': self.sectionname, 'sortorder': self.sortorder}
        return json.dumps(json_obj)

    def from_json(self, data):
        self.libid = data['libid']
        self.sectionname = data['sectionname']
        self.sortorder = data['sortorder']


class Subject(Base):
    '''定义试题
    '''

    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True)
    subjecttype = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    sectionid = Column(Integer, ForeignKey('section.id'))
    degree = Column(String(20), nullable=False)

    section = relationship('Section')

    def __init__(self, subjecttype=None, title=None, sectionid=None, degree=u'普通'):
        self.subjecttype = subjecttype
        self.title = title
        self.sectionid = sectionid
        self.degree = degree

    def json(self):
        json_obj = {'id': self.id, 'subjecttype': self.subjecttype, 'title': self.title,
                    'libid': self.section.libid, 'sectionid': self.sectionid, 'degree': self.degree}
        return json.dumps(json_obj)

    def from_json(self, data):
        self.subjecttype = data['subjecttype']
        self.title = data['title']
        self.sectionid = data['sectionid']
        self.degree = data['degree']


class Option(Base):
    '''定义试题的选项（选择题）
    '''

    __tablename__ = 'option'
    id = Column(Integer, primary_key=True)
    subjectid = Column(Integer, ForeignKey('subject.id'))
    title = Column(String(500), nullable=False)
    sortorder = Column(Integer)

    def __init__(self, subjectid=None, title=None, sortorder=110):
        self.subjectid = subjectid
        self.title = title
        self.sortorder = sortorder

    def json(self):
        json_obj = {'id': self.id, 'subjectid': self.subjectid,
                    'title': self.title, 'sortorder': self.sortorder}
        return json.dumps(json_obj)

    def from_json(self, data):
        self.subjectid = data['subjectid']
        self.title = data['title']
        self.sortorder = data['sortorder']


class Answer(Base):
    '''定义试题的答案
    '''

    __tablename__ = 'answer'
    id = Column(Integer, primary_key=True)
    subjectid = Column(Integer, ForeignKey('subject.id'))
    answervalue = Column(String(50), nullable=False)

    def __init__(self, subjectid=None, answervalue=None):
        self.subjectid = subjectid
        self.answervalue = answervalue

    def json(self):
        json_obj = {'id': self.id, 'subjectid': self.subjectid,
                    'answervalue': self.answervalue}
        return json.dumps(json_obj)

    def from_json(self, data):
        self.subjectid = data['subjectid']
        self.answervalue = data['answervalue']


class MarkedSubject(Base):
    '''定义用户标记的重点题
    '''

    __tablename__ = 'markedsubject'
    id = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey('user.id'))
    subjectid = Column(Integer, ForeignKey('subject.id'))

    def __init__(self, userid=None, subjectid=None):
        self.userid = userid
        self.subjectid = subjectid

    def json(self):
        json_obj = {'id': self.id, 'userid': self.userid,
                    'subjectid': self.subjectid}
        return json.dumps(json_obj)

    def from_json(self, data):
        self.userid = data['userid']
        self.subjectid = data['subjectid']


class ErrorSubject(Base):
    '''定义用户练习的错题记录
    '''

    __tablename__ = 'errorsubject'
    id = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey('user.id'))
    subjectid = Column(Integer, ForeignKey('subject.id'))
    count = Column(Integer)

    def __init__(self, userid=None, subjectid=None, count=1):
        self.userid = userid
        self.subjectid = subjectid
        self.count = count

    def json(self):
        json_obj = {'id': self.id, 'userid': self.userid,
                    'subjectid': self.subjectid, 'count': self.count}
        return json.dumps(json_obj)

    def from_json(self, data):
        self.userid = data['userid']
        self.subjectid = data['subjectid']
        self.count = data['count']


class ExamHistory(Base):
    '''用户练习的成绩记录
    '''

    __tablename__ = 'examhistory'
    id = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey('user.id'))
    datetime = Column(DateTime)
    total = Column(Integer)
    right = Column(Integer)
    error = Column(Integer)
    timeused = Column(Integer)  # 用时：以分钟计算
    examtype = Column(String(20))

    user = relationship('User')

    def __init__(self, userid=None, datetime=None, total=None, right=None, error=None, timeused=None, examtype=None):
        self.userid = userid
        self.datetime = datetime
        self.total = total
        self.right = right
        self.error = error
        self.timeused = timeused
        self.examtype = examtype

    def json(self):
        json_obj = {'id': self.id, 'userid': self.userid, 'username': self.user.username, 'datetime': self.datetime, 'total': self.total, 'right': self.right,
                    'error': self.error, 'timeused': self.timeused, 'examtype': self.examtype
                    }
        return json.dumps(json_obj)

    def from_json(self, data):
        self.userid = data['userid']
        self.datetime = data['datetime']
        self.total = data['total']
        self.right = data['right']
        self.error = data['error']
        self.timeused = data['timeused']
        self.examtype = data['examtype']
