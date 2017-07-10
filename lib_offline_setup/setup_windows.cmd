c:\python27\scripts\pip install Werkzeug-0.11.2-py2.py3-none-any.whl
c:\python27\scripts\pip install xlwt-1.1.2-py2.py3-none-any.whl

cd MarkupSafe-0.23
c:\python27\python setup.py install
cd  ..\itsdangerous-0.24
c:\python27\python setup.py install
cd ..
c:\python27\scripts\pip install Jinja2-2.8-py2.py3-none-any.whl
cd SQLAlchemy-1.0.9
c:\python27\python setup.py install
cd ..\Flask-0.10.1
c:\python27\python setup.py install
cd ..\Flask-Login-0.3.2
c:\python27\python setup.py install
cd ..\Flask-SQLAlchemy-2.1
c:\python27\python setup.py install
cd ..\xlrd-0.9.4
c:\python27\python setup.py install
cd ..

c:\python27\scripts\pip list