#-*- coding: utf-8 -*-
import random
import json
from sqlalchemy import text
from webexam.database import db_session
from webexam.models import *
from webexam.controls import *

class Exam():
    def __init__(self,instance,form=None):
        self.instance = instance
        self.form = form
    
    def parse_argument(self):
        index = 1
        args_data = []
        while True:
            subject_arg = {}
            subject_arg['libid'] = self.form.get('selLib_%d'%index,'')
            subject_arg['sectionid'] = self.form.get('selSection_%d'%index,'')
            subject_arg['subjecttype'] = self.form.get('selSubjectType_%s'%index,'')
            subject_arg['degree'] = self.form.get('selDegree_%s'%index,'')
            subject_arg['count'] = int(self.form.get('inputCount_%s'%index,0))
            subject_arg['optionRandom'] = self.form.get('optionRandom','false')
            #
            if subject_arg['libid'] == '' or subject_arg['sectionid'] == '':
                break
            sql_filter = []
            if subject_arg['sectionid'] != '0':
                sql_filter.append('sectionid==%s'%subject_arg['sectionid'])
            elif subject_arg['libid'] != '0':
                sql_filter.append('sectionid in ( select id from section where libid=%s)'%subject_arg['libid'])
            if subject_arg['subjecttype'] != '':
                sql_filter.append('subjecttype="%s"'%subject_arg['subjecttype'])
            if subject_arg['degree'] !='':
                sql_filter.append('degree="%s"'%subject_arg['degree'])
            if self.instance == 'errorsubject' or self.instance == 'markedsubject':
                userid = session['userid']
                sql_filter.append('id in (select subjectid from %s where userid=%s)'%(self.instance,userid))
            ###
            subject_arg['filter'] = ' and '.join(sql_filter)
            #
            if subject_arg['count'] >0:
                args_data.append(subject_arg)
            index += 1

        return args_data

    def get_option_and_answer(self,subject):
        #option
        options = []
        if subject['subjecttype'] == 'SingleSel' or subject['subjecttype'] == 'MultiSel':
            option_inst = List('option')
            option_inst.obj_instance['option']['filter'] = "subjectid==%s"%subject['id']
            option_rows =option_inst.gets(page=0)['rows']
            
            for row in option_rows:
                options.append(json.loads(row.json()))
        #answer
        answer_inst = List('answer')
        answer_inst.obj_instance['answer']['filter'] = "subjectid==%s"%subject['id']
        answer_obj = answer_inst.gets(page=0)['rows'][0]
        answer = answer_obj.answervalue if answer_obj is not None else ''
        #
        if self.optionRandom == 'true' and (subject['subjecttype'] == 'SingleSel' or subject['subjecttype'] == 'MultiSel'):
            answer = self.random_options(options,answer)
        #
        subject_data = {}
        subject_data['subject'] = subject
        subject_data['option'] = options
        subject_data['answer'] = answer

        return subject_data

    def random_options(self,options,answer):
        random.shuffle(options)
        answer_new = ''

        for a in answer:
            for index,option in enumerate(options):
                if option['sortorder'] == int(a) or option['sortorder'] == 100 + int(a):
                    answer_new += str(index+1)
                    break

        return ''.join(sorted(answer_new))

    def generate_subject(self,args=None):
        subject_data = []
        if args == None:
            args_data = self.parse_argument()
        else:
            args_data = args
        #
        for arg in args_data:
            self.optionRandom = arg['optionRandom']
            subject_inst = List('subject')
            subject_inst.obj_instance['subject']['filter'] = arg['filter']
            objs = subject_inst.gets(page=0)['rows']
            #
            json_subject_data = []
            for obj in objs:
                json_subject_data.append(json.loads(obj.json()))

            if self.instance == 'errorsubject':
                json_subject_data = self.__sort_by_errorcount(json_subject_data)
                subject_data.extend(json_subject_data[:arg['count']])
            else:
                random.shuffle(json_subject_data)
                subject_data.extend(random.sample(json_subject_data,arg['count']))

        return self.__sort_by_subjecttype(subject_data)

    def __sort_by_subjecttype(self,subjects):
        subjecttype=['Judge','SingleSel','MultiSel']
        ret_subject_data = []

        for stype in subjecttype:
            for sdata in subjects:
                if sdata['subjecttype'] == stype:
                    ret_subject_data.append(self.get_option_and_answer(sdata))

        return ret_subject_data

    def __sort_by_errorcount(self,subjects):
        if 'userid' not in session:
            return subjects

        errorsubject_load_inst = Load('errorsubject')
        for i in range(len(subjects)):
            errorsubject_obj = errorsubject_load_inst.get_user_subject(session['userid'],subjects[i]['id'])
            if errorsubject_obj =='':
                subjects[i]['count'] = 0
            else:
                subjects[i]['count'] = int(json.loads(errorsubject_obj)['count'])

        sorted_subjects = sorted(subjects,key=lambda x:x['count'],reverse=True)
        return sorted_subjects;

    def mark_subject(self,userid,subject_data):
        return self.__mark_or_remove_unmarked_subject(True,userid,subject_data)

    def remove_unmarked_subject(self,userid,subject_data):
        return self.__mark_or_remove_unmarked_subject(False,userid,subject_data)

    def __mark_or_remove_unmarked_subject(self,flag,userid,subject_data):
        '''flag->true:mark subject,flag->false:remove subject
        '''
        results = ''
        for subject in subject_data:
            marksubject_load_inst = Load('markedsubject')
            obj = marksubject_load_inst.get_user_subject(userid,subject['subjectid'])
            if obj == '' and flag:
               markedsubject_edit_inst = Edit('markedsubject')
               markedsubject_data ={'userid':userid,'subjectid':subject['subjectid']}
               results = markedsubject_edit_inst.save(markedsubject_data)
            elif not obj == '' and not flag:
                markedsubject_del_inst = Delete('markedsubject')
                obj = json.loads(obj)
                results = markedsubject_del_inst.delete(str(obj['id']))
        if results == '':
            results = json.dumps({'status':'ok','msg':u'标记/移除试题成功！'})

        return results;

    def update_error_subject(self,userid,subject_data):
        results = ''
        for subject in subject_data:
            errorsubject_load_inst = Load('errorsubject')
            obj = errorsubject_load_inst.get_user_subject(userid,subject['subjectid'])
            if obj == '':
                errorsubject_edit_inst = Edit('errorsubject')
                errorsubject_data ={'userid':userid,'subjectid':subject['subjectid'],'count':1}
                results = errorsubject_edit_inst.save(errorsubject_data)
            elif not obj == '' :
                errorsubject_update_inst = Update('errorsubject')
                obj = json.loads(obj)
                obj['count'] += 1
                results = errorsubject_update_inst.save(obj['id'],obj)
        if results == '':
            results = json.dumps({'status':'ok','msg':u'更新错题记录失败'})

        return results;
