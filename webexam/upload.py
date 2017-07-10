#-*- coding: utf-8 -*-
import os,datetime
import json
from sqlalchemy import text
from webexam.database import db_session
from webexam.models import *
from webexam.controls import *
import xlrd

class Upload():
    def __init__(self):
    	pass

    def save_file(self,f):
        filename = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')+'.xls'
        pathfile = os.getcwd()+'/webexam/static/upload/'+filename
        f.save(pathfile)

        return filename

    def parse_file(self,filename):
        pathfile = os.getcwd()+'/webexam/static/upload/'+filename
        xlsfile = xlrd.open_workbook(pathfile)
        sheet = xlsfile.sheets()[0]
        subject_data =[]
        for row in range(1,sheet.nrows):
            subject = {}
            subject['subjecttypename'] = sheet.cell(row,0).value
            if subject['subjecttypename'] == None or subject['subjecttypename'] == '':
                break
            subject['libname'] = sheet.cell(row,1).value
            subject['sectionname'] = sheet.cell(row,2).value
            subject['degreename'] = sheet.cell(row,3).value
            subject['title'] = sheet.cell(row,4).value
            subject['answer'] = sheet.cell(row,5).value
            if subject['subjecttypename'] == u'单选题' or subject['subjecttypename'] == u'多选题':
                subject['option'] = []
                sortorder = 101
                for col in range(6,sheet.ncols):
                    option = {'subjectid':0}
                    option['title'] = sheet.cell(row,col).value
                    if option['title'] == None or option['title'] == '':
                    	break
                    option['sortorder'] = sortorder
                    subject['option'].append(option)
                    sortorder +=1
                subject['option_all'] = "$$".join([unicode(x['title']) for x in subject['option']])
            else:
            	subject['option_all'] = ''
            subject['info'] = ''
            self.verify_subject_data(subject)
            if subject['info'] == '':
                subject['info'] = 'ok'

            subject_data.append(subject)

        return subject_data

    def verify_subject_data(self,subject):
        #subjecttype
        subjecttype={u'单选题':'SingleSel',u'多选题':'MultiSel',u'判断题':'Judge'}
        if not subject['subjecttypename'] in subjecttype:
            subject['info'] += u' 类型不正确 '
            return False
        subject['subjecttype'] = subjecttype.get(subject['subjecttypename'])
        #lib
        instance_lib = Load('lib')
        obj_lib = instance_lib.get_by_name(subject['libname'])
        if obj_lib == '':
            subject['info'] +=u' 题库不正确 '
            return False
        obj_lib = json.loads(obj_lib)
        subject['libid'] = obj_lib['id']
        #section
        instance_section = Load('section')
        obj_section= instance_section.get_section(subject['libid'],subject['sectionname'])
        if obj_section == '':
            subject['info'] += u' 章节不正确 '
            return False
        obj_section = json.loads(obj_section)
        subject['sectionid'] = obj_section['id']
        #degree
        degree = {u'容易':'easy',u'普通':'normal',u'困难':'hard'}
        if not subject['degreename'] in degree:
            subject['info'] += u' 困难度不正确 '
            return False
        subject['degree'] = degree.get(subject['degreename'])
        #title
        if subject['title'] == None or subject['title'] == '':
            subject['info'] += u' 题目不正确 '
            return False
        #answer
        if subject['answer'] == None or subject['answer'] == '':
            subject['info'] += u' 答案不正确 '
            return False
        answer_judge = {u'是':'True',u'正确':'True',u'对':'True',u'否':'False',u'错误':'False',u'错':'False',\
                        u'TRUE':'True',u'True':'True',u'true':'True',u'FALSE':'False',u'False':'False',u'false':'False'
        }
        answer_sel = {'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,
                      '1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8
        }
        if subject['subjecttype'] == 'Judge':
            if not subject['answer'] in answer_judge:
                subject['info'] += u' 答案不正确 '
                return False
            subject['answervalue'] = answer_judge.get(subject['answer'])
        else:
            a = subject['answer'].lower()
            b = []
            for x in a :
                if x in answer_sel:
                    b.append(answer_sel.get(x))
            if len(b) == 0 or max(b)>len(subject['option']):
                subject['info'] += u' 答案不正确 '
                return False
            subject['answervalue'] = ''.join([str(c) for c in b])
        #option
        #option dont't need verify

        return True

    def save_subject(self,subject_data):
        for subject in subject_data:
            #save subject
            subject_instance = Edit('subject')
            try:
                results_subject = json.loads(subject_instance.save(subject))
                if results_subject['status'] == 'ok' :
                    #save option
                    if subject['subjecttype'] == 'SingleSel' or subject['subjecttype'] == 'MultiSel':
                        for i in range(len(subject['option'])):
                            subject['option'][i]['subjectid'] = results_subject['id']
                        option_instance = Edit('option')
                        try:
                            results_option = json.loads(option_instance.save(subject['option']))
                            #set the option id of answer
                            if results_option['status'] != 'ok':
                                subject['info'] = u'保存选项失败'
                                continue
                        except:
                            subject['info'] = u'保存选项失败'
                            continue
                    # end if subject['subjecttype'] == 'SingleSel' ...
                    #save answer:
                    answer_obj = {'subjectid':results_subject['id'],'answervalue':subject['answervalue']}
                    answer_instance = Edit('answer')
                    try:
                        results_answer = json.loads(answer_instance.save(answer_obj))
                        if results_answer['status'] == 'ok':
                            subject['info'] = 'ok'
                        else:
                            subject['info'] = u'保存答案失败'
                            continue
                    except:
                        subject['info'] = u'保存答案失败'
                #end if results_subject['status'] == 'ok'
                else:
                    subject['info'] = u'保存试题失败'
                    continue
            #end try
            except:
                subject['info'] = u'保存试题失败'

        return subject_data
