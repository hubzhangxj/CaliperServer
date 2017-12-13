# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class User(models.Model):
    username = models.CharField(max_length=50,null=False,unique=True)  #用户名
    name = models.CharField(max_length=255, null=True)
    role = models.IntegerField(null=False) #用户角色 0-admin 1-普通用户
    createtime = models.DateTimeField(auto_created=True)  #创建时间
    company = models.CharField(max_length=255, blank=True, null=True) #公司名称
    address = models.CharField(max_length=255, blank=True, null=True) #公司地址

    class Meta:
        managed = False
        db_table = 'user'
