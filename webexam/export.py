#-*- coding: utf-8 -*-
import json
from webexam.database import db_session
from webexam.models import *
from webexam.controls import *

class Export():
    def __init__(self, args=None):
        self.args = args

    def export(self, id):
        ids = id.split(',')
        export_subjects = []
        try:
            for _id in ids:
                lib = Load('lib').get(_id)
                sections = List('section',{'libid':_id}).gets(page=0)['rows']
                for _sec in  sections:
                    _sec_obj = json.loads(_sec.json())
                    export_subjects.extend(self.get_subject(_sec_obj['libname'],_sec_obj['sectionname'],str(_sec_obj['id'])))
            
            self.export_to_xls(export_subjects)
            return json.dumps({'status': 'ok', 'msg': u'导出成功！'})

        except Exception,ex:
            return json.dumps({'status': 'fail', 'msg': u'导出失败:%s'%ex.message})


    def export_errorsubject(self,id):
        ids = id.split(',')
        export_subjects = []
        try:
            for _id in ids:
                lib = json.loads(Load('lib').get(_id))
                obj_list = List('errorsubject',{'libid':str(_id)})
                rows = obj_list.gets(page=0)['rows']
                for obj in rows:
                    sub_obj = json.loads(obj.json())
                    #
                    section = json.loads(Load('section').get(sub_obj['sectionid']))
                    sub_obj['libname'] = lib['libname']
                    sub_obj['sectionname'] = section['sectionname']
                    self.get_option_and_answer(sub_obj)
                    #
                    export_subjects.append(sub_obj)

            self.export_to_xls(export_subjects)
            return json.dumps({'status': 'ok', 'msg': u'导出成功！'})

        except Exception,ex:
            #raise
            return json.dumps({'status': 'fail', 'msg': u'导出失败:%s'%ex.message})


    def get_subject(self,libname,sectionname,sectionid):
        subject_inst = List('subject',{'sectionid':str(sectionid)})
        objs = subject_inst.gets(page=0)['rows']
        
        export_subjects = []
        for obj in objs:
            sub_obj = json.loads(obj.json())
            sub_obj['libname'] = libname
            sub_obj['sectionname'] = sectionname
            self.get_option_and_answer(sub_obj)

            export_subjects.append(sub_obj)

        return export_subjects
            
        
    def get_option_and_answer(self,subject):
        #option
        if subject['subjecttype'] == 'SingleSel' or subject['subjecttype'] == 'MultiSel':
            option_inst = List('option')
            option_inst.obj_instance['option']['filter'] = "subjectid==%s"%subject['id']
            option_rows =option_inst.gets(page=0)['rows']
            subject['option']=[]
            
            for row in option_rows:
                subject['option'].append(json.loads(row.json()))
        #answer
        answer_inst = List('answer')
        answer_inst.obj_instance['answer']['filter'] = "subjectid==%s"%subject['id']
        answer_obj = answer_inst.gets(page=0)['rows'][0]
        subject['answer'] = answer_obj.answervalue if answer_obj is not None else ''

    def export_to_xls(self,subjects):
        import xlwt

        wb = xlwt.Workbook()
        ws = wb.add_sheet('export')
        ws.write(0,0,u'题型')
        ws.write(0,1,u'题库名称')
        ws.write(0,2,u'章节名称')
        ws.write(0,3,u'困难度')
        ws.write(0,4,u'试题内容')
        ws.write(0,5,u'答案')
        ws.write(0,6,u'选项')
        index = 1
        for subject in subjects:
            ws.write(index, 0, self.replace_subjecttype(subject['subjecttype']))
            ws.write(index, 1, subject['libname'])
            ws.write(index, 2, subject['sectionname'])
            ws.write(index, 3, self.replace_subject_degree(subject['degree']))
            ws.write(index, 4, subject['title'])
            ws.write(index, 5, self.replace_answer_text(subject['subjecttype'],subject['answer']))
            option_index = 6
            
            if subject['subjecttype'] == 'SingleSel' or subject['subjecttype'] == 'MultiSel':
                for o in subject['option']:
                    ws.write(index,option_index,o['title'])
                    option_index += 1

            index += 1

        wb.save('webexam/static/export/export.xls')
        print 'export subject done ...'

    def replace_answer_text(self,subjecttype,answer):
        if subjecttype == 'Judge':
            return u'正确' if answer == 'True' else u'错误'
        else:
            for i in range(1,10):
                answer = answer.replace(str(i),chr(ord('A')+i-1))
            return answer

    def replace_subjecttype(self,subjecttype):
        subjecttypes = {'Judge':u'判断题','SingleSel':u'单选题','MultiSel':u'多选题'}
        return subjecttypes.get(subjecttype,'')

    def replace_subject_degree(self,degree):
        degrees = {'easy':u'容易','normal':u'普通','hard':u'困难'}
        return degrees.get(degree,'')
        