# webexam v2.3

** 理论考试的客观题自由练习系统 **

* last update : 2017-06-26

### 1.依赖组件安装

+ python 2.7和pip
+ Flask 
+ Flask-Login 
+ Flask-SQLAlchemy 
+ xlrd
+ xlwt
 
		在线安装：
		安装了python后，使用pip安装：
		pip install flask flask-login flask-sqlalchemy xlrd xlwt
		
		离线安装：
		在windows下可以使用离线包安装，在命令符窗口，进入到webexam/lib_offline_setup，运行setup_windows.cmd批处理自动安装。

### 2.使用

+ 在命令行窗口中，进入webexam目录，运行python runserver.py
+ 打开浏览器，输入http://localhost:5000
+ 前端页面使用了bootstrap，支持多种浏览器和手机端自适应（建议使用chrome浏览器以获得最好的效果）
+ 目前只支持单选、多选和判断题的练习，可以将excel格式的试题进行导入（导入模板可以导入页面下载）。
+ 支持将题库导出为xls文件，增加了错误试题导出功能。
+ 练习时可以将选择题选项随机。