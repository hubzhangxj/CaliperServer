#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os

reload(sys)
sys.setdefaultencoding('utf8')

#  1.删除所有模块migrations文件夹下除__init__.py外的其他所有文件
#  2.再修改model前,先执行 python manage.py makemigrations
#  3.继续执行python manage.py migrate --fake
#  4.修改model,然后执行 python manage.py makemigrations
#  5.执行python manage.py migrate
import MySQLdb as db
import manage

base_path = sys.path[0]

def read_dir(dir):
    """
    删除migrations 文件夹下的所有非__init__.py文件
    :param dir:
    :return:
    """
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in dirs:
            if name == "migrations":
                c_path = os.path.join(root,name)
                for c_root, c_dirs, c_files in os.walk(c_path, topdown=False):
                    for file in c_files:
                        if file !=  '__init__.py':
                            file_path = os.path.join(c_root,file)
                            os.remove(file_path)

read_dir(base_path)

con = None
try:
    # 连接 mysql 的方法： connect('ip','user','password','dbname')
    con = db.connect('192.168.64.97', 'caliper', 'root', 'root')

    # 所有的查询，都在连接 con 的一个模块 cursor 上面运行的
    cur = con.cursor()

    # 执行一个查询
    cur.execute("delete from django_migrations")
    con.commit()
except Exception as e:
    print "=============="
    print e
finally:
    if con:
        # 无论如何，连接记得关闭
        con.close()


os.system("python manage.py makemigrations")

os.system("python manage.py migrate --fake")

print "please modify your models:"
print "When you finish modify,please input 'y'"
y = raw_input()

if y == 'y':
    os.system("python manage.py makemigrations")

    os.system("python manage.py migrate")