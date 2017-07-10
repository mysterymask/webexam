#!/usr/bin/env python
#-*- coding: utf-8 -*-
import json
import os
from flask import Flask, request, session, redirect, url_for, render_template
from flask.ext.login import login_required
from webexam import app
from webexam.database import db_session
from webexam.controls import *
from webexam.upload import *
from webexam.exam import *
from webexam.export import *

app.secret_key = os.urandom(24)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def index():
    return render_template('login.html', title=u'webexam登录')


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    us = UserSession()
    if us.login(username, password):
        return redirect(url_for('exam_start', instance='subject'))
    else:
        return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    us = UserSession()
    us.logout()
    return redirect(url_for('index'))


@app.route('/admin/<instance>/count', methods=['GET'])
def count(instance):
    results = ''
    if instance == 'markedsubject' or instance == 'errorsubject':
        if 'userid' not in session:
            return json.dumps({'status': 'fail', 'msg': u'读取试题数量失败：会话已过期！', 'total_rows': 0})

    obj_instance = List(instance, request.args)
    results = obj_instance.count()

    return results


@app.route('/admin/<instance>/list/<page>', methods=['GET'])
@login_required
def list(instance, page):
    obj_instance = List(instance, request.args)
    results = obj_instance.gets(page)

    return render_template(instance + '.html', results=results, title=u'管理-WebExam')


@app.route('/admin/<instance>/load/<id>', methods=['GET', 'POST'])
def load(instance, id):
    obj_instance = Load(instance)
    return obj_instance.get(id)


@app.route('/admin/<instance>/loads', methods=['GET'])
def loads(instance):
    obj_instance = List(instance, request.args)
    results = obj_instance.gets(page=0)
    data = []
    for row in results['rows']:
        data.append(json.loads(row.json()))

    return json.dumps(data)


@app.route('/admin/<instance>/edit', methods=['POST'])
@login_required
def edit(instance):
    obj_instance = Edit(instance)
    json_data = request.get_json()
    if instance == 'examhistory':
        if 'userid' in session:
            json_data['userid'] = session['userid']
            json_data['datetime'] = datetime.datetime.now()
        else:
            return json.dumps({'status': 'fail', 'msg': u'保存练习历史记录失败：会话已过期！', 'id': 0})
    return obj_instance.save(json_data)


@app.route('/admin/<instance>/update/<id>', methods=['POST'])
@login_required
def update(instance, id):
    obj_instance = Update(instance)
    return obj_instance.save(id, request.get_json())


@app.route('/admin/<instance>/delete/<id>', methods=['GET'])
@login_required
def delete(instance, id):
    obj_instance = Delete(instance)
    return obj_instance.delete(id)


@app.route('/admin/<instance>/delall', methods=['GET'])
@login_required
def delall(instance):
    obj_instance = Delete(instance, request.args)
    results = obj_instance.delete_all()
    return results


@app.route('/admin/subject/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'GET':
        return render_template('upload.html', title=u'试题导入')
    elif request.method == 'POST':
        obj_instance = Upload()
        filename = obj_instance.save_file(request.files['input_file'])
        subject_data = obj_instance.parse_file(filename)
        subject_ok = 0
        for subject in subject_data:
            if subject['info'] == 'ok':
                subject_ok += 1

        return render_template('upload.html', subject_data=subject_data, filename=filename, subject_total=len(subject_data), subject_ok=subject_ok, title=u'试题导入')


@app.route('/admin/subject/upload/<filename>', methods=['GET'])
@login_required
def upload_import(filename):
    obj_instance = Upload()
    subject_data = obj_instance.save_subject(obj_instance.parse_file(filename))
    subject_data = obj_instance.parse_file(filename)
    subject_ok = 0
    for subject in subject_data:
        if subject['info'] == 'ok':
            subject_ok += 1

    return render_template('upload.html', subject_data=subject_data, subject_total=len(subject_data), subject_ok=subject_ok)


@app.route('/exam/<instance>/start', methods=['GET'])
@login_required
def exam_start(instance):
    return render_template('exam_start.html', instance=instance, title=u'练习-WebExam')


@app.route('/exam/<instance>/test', methods=['GET', 'POST'])
@login_required
def exam_test(instance):
    if request.method == 'GET':
        return render_template('exam_test.html', instance=instance, title=u'WebExam-练习')
    elif request.method == 'POST':
        exam = Exam(instance, request.form)
        args_data = exam.parse_argument()
        session['args_data'] = args_data

        return redirect(url_for('exam_test', instance=instance))


@app.route('/exam/<instance>/get_subjectdata')
@login_required
def exam_test_subjectdata(instance):
    subject_data = ''
    if 'args_data' in session:
        exam = Exam(instance)
        subject_data = exam.generate_subject(session['args_data'])
        escape_html = {'<': '&lt;', '>': '&gt;', '\'': '&#44;', '"': '&quot;'}
        for i in range(len(subject_data)):
            for k, v in escape_html.items():
                subject_data[i]['subject']['title'] = subject_data[
                    i]['subject']['title'].replace(k, v)
                if subject_data[i].get('option') == None:
                    continue
                for m in range(len(subject_data[i]['option'])):
                    subject_data[i]['option'][m]['title'] = subject_data[
                        i]['option'][m]['title'].replace(k, v)

    return json.dumps(subject_data)


@app.route('/admin/markedsubject/<action>', methods=['POST'])
def mark_subject(action):
    if 'userid' in session:
        userid = session['userid']
        subject_data = request.get_json()
        exam_inst = Exam('markedsubject')
        if action == 'mark':
            results = exam_inst.mark_subject(userid, subject_data)
        elif action == 'remove':
            results = exam_inst.remove_unmarked_subject(userid, subject_data)
    else:
        results = json.dumps({'status': 'fail', 'msg': u'保存/移除标记试题失败：会话已过期！'})

    return results


@app.route('/admin/errorsubject/update', methods=['POST'])
def update_error_subject():
    if 'userid' in session:
        userid = session['userid']
        subject_data = request.get_json()
        exam_inst = Exam('errorsubject')
        results = exam_inst.update_error_subject(userid, subject_data)
    else:
        results = json.dumps({'status': 'fail', 'msg': u'更新错题记录失败：会话已过期！'})

    return results

@app.route('/admin/lib/export/<id>', methods=['GET'])
@login_required
def export(id):
    obj = Export()
    return obj.export(id)

@app.route('/admin/lib/export_errorsubject/<id>', methods=['GET'])
@login_required
def export_errorsubject(id):
    obj = Export()
    return obj.export_errorsubject(id)
