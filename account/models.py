# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class User(models.Model):
    username = models.CharField(max_length=50,null=False,unique=True)  #用户名
    name = models.CharField(max_length=255, null=True)
    role = models.IntegerField(null=False) #用户角色 0-admin 1-普通用户
    createtime = models.DateTimeField(auto_created=True)  #创建时间
    company = models.CharField(max_length=255, blank=True, null=True) #公司名称
    address = models.CharField(max_length=255, blank=True, null=True) #公司地址
    email=models.CharField(max_length=50,null=True) #邮箱
    telphone = models.CharField(max_length=50,null=True) #手机

    class Meta:
        db_table = 'user'
