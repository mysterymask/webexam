#!/usr/bin/env python
#-*- coding: utf-8 -*-
from flask import Flask
from flask.ext.login import LoginManager

app = Flask(__name__)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = '/'
login_manager.init_app(app)

import webexam.views
