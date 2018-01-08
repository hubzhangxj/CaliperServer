# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser

import os
from uuid import uuid4

def path_and_rename(instance, filename):
    upload_to = 'avatars'
    ext = filename.split('.')[-1]
    # get filename
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        # set filename as random string
        filename = '{}.{}'.format(uuid4().hex, ext)
    # return the whole path to the file
    return os.path.join(upload_to, filename)

class UserProfile(AbstractUser):
    avatar = models.ImageField(upload_to=path_and_rename, null=True, blank=True)  # 头像
    name = models.CharField(max_length=255, null=True)
    role = models.IntegerField(null=False,default=1) #用户角色 0-admin 1-普通用户
    # createtime = models.DateTimeField(auto_created=True)  #创建时间
    company = models.CharField(max_length=255, blank=True, null=True) #公司名称
    address = models.CharField(max_length=255, blank=True, null=True) #公司地址
    telphone = models.CharField(max_length=50,null=True) #手机

    class Meta:
        db_table = 'userProfile'
