# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser

class UserProfile(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)  # 头像
    name = models.CharField(max_length=255, null=True)
    role = models.IntegerField(null=False,default=1) #用户角色 0-admin 1-普通用户
    # createtime = models.DateTimeField(auto_created=True)  #创建时间
    company = models.CharField(max_length=255, blank=True, null=True) #公司名称
    address = models.CharField(max_length=255, blank=True, null=True) #公司地址
    telphone = models.CharField(max_length=50,null=True) #手机

    class Meta:
        db_table = 'userProfile'
