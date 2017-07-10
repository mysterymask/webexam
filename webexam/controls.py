#!/usr/bin/env python
#-*- coding: utf-8 -*-
import math
import json
from sqlalchemy import text
from webexam.database import db_session
from webexam.models import *
from flask import session
from flask.ext.login import login_user, logout_user

ROWS_PER_PAGE = 20


class List():

    def __init__(self, instance, args=None):
        self.instance = instance
        self.obj_instance = {'lib': {'instance': Lib, 'filter': '', 'sort': Lib.sortorder.desc()},
                             'section': {'instance': Section, 'filter': '', 'sort': Section.sortorder.desc()},
                             'subject': {'instance': Subject, 'filter': '', 'sort': Subject.title},
                             'user': {'instance': User, 'filter': '', 'sort': User.sortorder.desc()},
                             'option': {'instance': Option, 'filter': '', 'sort': Option.sortorder},
                             'answer': {'instance': Answer, 'filter': '', 'sort': Answer.id},
                             'markedsubject': {'instance': Subject, 'filter': '', 'sort': Subject.id},
                             'errorsubject': {'instance': Subject, 'filter': '', 'sort': Subject.id},
                             'examhistory': {'instance': ExamHistory, 'filter': '', 'sort': ExamHistory.datetime.desc()}
                             }
        self.results = {}
        self.results['page_info'] = self.results['rows'] = {}
        if args is not None:
            if instance == 'section':
                libid = args.get('libid', '0')
                if libid != '0':
                    self.obj_instance['section'][
                        'filter'] = 'libid==%s' % libid
                self.results['page_info']['libid'] = libid
            elif instance == 'subject':
                sql_filter = self.__get_subject_filter(args)
                self.obj_instance['subject'][
                    'filter'] = ' and '.join(sql_filter)
            elif instance == 'option' or instance == 'answer':
                subjectid = args.get('subjectid', '0')
                self.obj_instance[instance][
                    'filter'] = 'subjectid==%s' % subjectid
            elif instance == 'errorsubject' or instance == 'markedsubject':
                sql_filter = self.__get_subject_filter(args)
                userid = session['userid']
                sql_filter.append(
                    'id in (select subjectid from %s where userid=%s)' % (instance, userid))
                self.obj_instance[instance][
                    'filter'] = ' and '.join(sql_filter)

    def gets(self, page):
        if self.instance in self.obj_instance:
            obj = self.obj_instance.get(self.instance)
            if int(page) == 0:
                self.results['rows'] = obj['instance'].query\
                    .filter(text(obj['filter']))\
                    .order_by(obj['sort']).all()
            else:
                page = int(page) if page >= 1 else 1
                self.results['page_info']['page'] = page
                self.__get_lists(obj, page)

        return self.results

    def __get_subject_filter(self, args):
        self.results['page_info']['libid'] = args.get('libid', '0')
        self.results['page_info']['sectionid'] = args.get('sectionid', '0')
        self.results['page_info']['subjecttype'] = args.get('subjecttype', '')
        self.results['page_info']['title'] = args.get('title', '')
        self.results['page_info']['degree'] = args.get('degree', '')
        sql_filter = []
        if self.results['page_info']['sectionid'] != '0':
            sql_filter.append('sectionid==%s' %
                              self.results['page_info']['sectionid'])
        elif self.results['page_info']['libid'] != '0':
            sql_filter.append('sectionid in ( select id from section where libid=%s)' % self.results[
                              'page_info']['libid'])
        if self.results['page_info']['subjecttype'] != '':
            sql_filter.append('subjecttype="%s"' %
                              self.results['page_info']['subjecttype'])
        if self.results['page_info']['title'] != '':
            sql_filter.append('title like "%%%s%%"' %
                              self.results['page_info']['title'])
        if self.results['page_info']['degree'] != '':
            sql_filter.append('degree="%s"' %
                              self.results['page_info']['degree'])

        return sql_filter

    def __get_lists(self, obj, page):
        self.results['page_info']['total_rows'] = obj[
            'instance'].query.filter(text(obj['filter'])).count()
        self.results['page_info']['total_pages'] = int(
            math.ceil(self.results['page_info']['total_rows'] / (ROWS_PER_PAGE * 1.0)))
        if self.results['page_info']['total_pages'] == 0:
            self.results['page_info']['total_pages'] = 1
        if page > self.results['page_info']['total_pages']:
            self.results['page_info']['page'] = self.results[
                'page_info']['total_pages']
        else:
            self.results['page_info']['page'] = page

        self.results['rows'] = obj['instance'].query\
            .filter(text(obj['filter']))\
            .order_by(obj['sort'])\
            .offset(ROWS_PER_PAGE * (self.results['page_info']['page'] - 1))\
            .limit(ROWS_PER_PAGE)

    def count(self):
        total_rows = 0
        if self.instance in self.obj_instance:
            obj = self.obj_instance.get(self.instance)
            total_rows = obj['instance'].query.filter(
                text(obj['filter'])).count()

        return json.dumps({'total_rows': total_rows})


class Load():

    def __init__(self, instance):
        self.instance = instance
        self.obj_instance = {'lib': Lib, 'section': Section, 'subject': Subject, 'user': User, 'answer': Answer,
                             'markedsubject': MarkedSubject, 'errorsubject': ErrorSubject
                             }

    def get(self, id):
        results = ""
        if self.instance in self.obj_instance:
            obj = self.obj_instance.get(self.instance).query.filter(
                text('id==%s' % id)).first()
            results = "" if obj == None else obj.json()

        return results

    def get_by_name(self, name):
        results = ''
        if self.instance in self.obj_instance:
            obj = self.obj_instance.get(self.instance).query.filter(
                text('%sname=="%s"' % (self.instance, name))).first()
            results = '' if obj == None else obj.json()

        return results

    def get_section(self, libid, name):
        results = ''
        if self.instance == 'section' and self.instance in self.obj_instance:
            obj = self.obj_instance.get(self.instance).query.filter(
                text('libid==%s and sectionname=="%s"' % (libid, name))).first()
            results = '' if obj == None else obj.json()

        return results

    def get_user_subject(self, userid, subjectid):
        results = ''
        if self.instance == 'markedsubject' or self.instance == 'errorsubject':
            if self.instance in self.obj_instance:
                obj = self.obj_instance.get(self.instance).query.filter(
                    text('userid==%s and subjectid=="%s"' % (userid, subjectid))).first()
                results = '' if obj == None else obj.json()

        return results


class Edit():

    def __init__(self, instance):
        self.instance = instance
        self.obj_instance = {'lib': Lib(), 'section': Section(), 'subject': Subject(), 'user': User(), 'option': Option(),
                             'answer': Answer(), 'markedsubject': MarkedSubject(), 'errorsubject': ErrorSubject(), 'examhistory': ExamHistory()
                             }

    def save(self, data):
        results = ''
        if self.instance in self.obj_instance:
            if self.instance == 'option':
                return self.__save_options(data)
            try:
                obj = self.obj_instance.get(self.instance)
                obj.from_json(data)
                db_session.add(obj)
                db_session.commit()
                results = json.dumps(
                    {'status': 'ok', 'msg': u'保存已成功', 'id': obj.id})
            except:
                results = json.dumps({'status': 'fail', 'msg': u'保存时发生错误！'})
                raise

        return results

    def __save_options(self, data):
        ret_id = []
        for one_data in data:
            obj = Option()
            obj.from_json(one_data)
            db_session.add(obj)
            db_session.commit()
            ret_id.append(obj.id)

        results = json.dumps({'status': 'ok', 'msg': u'保存已成功', 'id': ret_id})
        return results


class Update():

    def __init__(self, instance):
        self.instance = instance
        self.obj_instance = {'lib': Lib, 'section': Section, 'subject': Subject, 'user': User,  'option': Option,
                             'answer': Answer, 'errorsubject': ErrorSubject
                             }

    def save(self, id, data):
        results = ''
        if self.instance in self.obj_instance:
            try:
                obj = self.obj_instance.get(self.instance).query.filter(
                    text('id==%s' % id)).scalar()
                if obj != None:
                    obj.from_json(data)
                    db_session.commit()
                    results = json.dumps(
                        {'status': 'ok', 'msg': u'更新已成功', 'id': obj.id})
                else:
                    results = json.dumps(
                        {'status': 'fail', 'msg': u'指定ID的记录不存在'})
            except:
                results = json.dumps({'status': 'fail', 'msg': u'更新时发生错误！'})

        return results


class Delete():

    def __init__(self, instance, args=None):
        self.instance = instance
        self.obj_instance = {'lib': Lib, 'section': Section, 'subject': Subject, 'user': User, 'option': Option,
                             'answer': Answer, 'markedsubject': MarkedSubject, 'errorsubject': ErrorSubject, 'examhistory': ExamHistory
                             }
        self.args = args

    def delete(self, id):
        ids = id.split(',')
        try:
            for _id in ids:
                if self.instance == 'lib':
                    self.__delete_lib_related(_id)
                elif self.instance == 'section':
                    self.__delete_seciton_related(_id)
                elif self.instance == 'subject':
                    self.__delete_subject_option_and_other(_id)
                elif self.instance == 'user':
                    self.__delete_user_subject_and_other(_id)

                obj = self.obj_instance.get(self.instance).query.filter(text('id==%s' % _id)).first()
                db_session.delete(obj)

            db_session.commit()
            print obj
            return json.dumps({'status': 'ok', 'msg': u'记录删除成功！'})
        except:
            return json.dumps({'status': 'fail', 'msg': u'记录删除失败！'})

    def delete_all(self):
        if (self.instance == 'option' or self.instance == 'answer') and not self.args == None:
            subject_id = self.args.get('subjectid', '')
            if not subject_id == '':
                try:
                    self.obj_instance.get(self.instance).query.filter(
                        text('subjectid==%s' % subject_id)).delete(synchronize_session=False)
                    db_session.commit()
                    return json.dumps({'status': 'ok', 'msg': u'记录删除成功！'})
                except:
                    return json.dumps({'status': 'fail', 'msg': u'记录删除失败！'})

    def __delete_lib_related(self,lib_id):
        '''
        级联删除题库相关联数据
        '''
        
        obj = self.obj_instance.get('section').query.filter(text('libid==%s' % lib_id)).all()
        for a_obj in obj:
            self.__delete_seciton_related(a_obj.id)
            self.obj_instance.get('section').query.filter(text('id==%s' % a_obj.id)).delete(synchronize_session=False)
            db_session.commit()

    def __delete_seciton_related(self,section_id):
        '''
        级联删除章节关联数据
        '''
        obj = self.obj_instance.get('subject').query.filter(text('sectionid==%s' % section_id)).all()
        for a_obj in obj:
            self.__delete_subject_option_and_other(a_obj.id)
            self.obj_instance.get('subject').query.filter(text('id==%s' % a_obj.id)).delete(synchronize_session=False)
            db_session.commit()

    def __delete_subject_option_and_other(self,subject_id):
        self.obj_instance.get('option').query.filter(
            text('subjectid==%s' % subject_id)).delete(synchronize_session=False)
        self.obj_instance.get('answer').query.filter(
            text('subjectid==%s' % subject_id)).delete(synchronize_session=False)
        self.obj_instance.get('markedsubject').query.filter(
            text('subjectid==%s' % subject_id)).delete(synchronize_session=False)
        self.obj_instance.get('errorsubject').query.filter(
            text('subjectid==%s' % subject_id)).delete(synchronize_session=False)
        db_session.commit()

    def __delete_user_subject_and_other(self,user_id):
        self.obj_instance.get('errorsubject').query.filter(
            text('userid==%s' % user_id)).delete(synchronize_session=False)
        self.obj_instance.get('markedsubject').query.filter(
            text('userid==%s' % user_id)).delete(synchronize_session=False)
        self.obj_instance.get('examhistory').query.filter(
            text('userid==%s' % user_id)).delete(synchronize_session=False)
        db_session.commit()
        
class UserSession():

    def __init__(self):
        pass

    def login(self, username, password):
        if username == '' or password == '':
            return False
        user_obj = User.query.filter(User.username == username).first()
        if user_obj is None or not user_obj.verify_password(password):
            return False
        session['username'] = user_obj.username
        session['userrole'] = user_obj.role
        session['userid'] = user_obj.id

        login_user(user_obj)

        return True

    def logout(self):
        session.pop('username', None)
        session.pop('userrole', None)
        session.pop('userid', None)

        logout_user()
