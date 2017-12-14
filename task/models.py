# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from account.models import User


# Create your models here.
class Baseboard(models.Model):  # 主板
    name = models.CharField(max_length=50, null=False)  # 主板名称
    manufacturer = models.CharField(max_length=200, blank=True, null=True)  # 制造商
    version = models.CharField(max_length=50, blank=True, null=True)  # 主板版本

    class Meta:
        db_table = 'baseboard'


class Cache(models.Model):  # 缓存
    socketdes = models.CharField(max_length=255, blank=True, null=True)  # 缓存级别
    size = models.CharField(max_length=50)  # 缓存大小
    operational = models.CharField(max_length=255, blank=True, null=True)  # 运作模式

    class Meta:
        db_table = 'cacheInfo'


class System(models.Model):  # 系统
    name = models.CharField(max_length=50, null=False)  # 系统名称
    manufacturer = models.CharField(max_length=200, blank=True, null=True)  # 制造商
    version = models.CharField(max_length=50, blank=True, null=True)  # 系统版本

    class Meta:
        db_table = 'system'


class Config(models.Model):  # 配置表
    hostname = models.CharField(max_length=50, blank=True, null=True)  # 测试名称
    kernel = models.CharField(max_length=50, blank=True, null=True)  # kernel 名称
    cache = models.ForeignKey(Cache)  # 缓存
    board = models.ForeignKey(Baseboard)  # 主板
    sys = models.ForeignKey(System)  # 系统
    os = models.CharField(max_length=50, null=True, blank=True)  # 系统名称

    class Meta:
        db_table = 'config'


class Cpu(models.Model):  # Cpu
    socketdes = models.CharField(max_length=50, blank=True, null=True)  # cpu 几级
    manufacturer = models.CharField(max_length=50, blank=True, null=True)  # 制造商
    version = models.CharField(max_length=50, blank=True, null=True)  # 版本
    maxspeed = models.CharField(max_length=50, blank=True, null=True)  # 最大速度
    currentspeed = models.CharField(max_length=50, blank=True, null=True)  # 当前速度
    status = models.CharField(max_length=50, blank=True, null=True)  # 状态
    corecount = models.IntegerField()  # 核心数目
    enabledCore = models.IntegerField()  # 有效核心数
    threadcount = models.IntegerField()  # 线程数
    config = models.ForeignKey(Config)  # 配置

    class Meta:
        db_table = 'cpu'


class Memory(models.Model):  # 内存
    manufacturer = models.CharField(max_length=255, blank=True, null=True)  # 制造商
    size = models.IntegerField()  # 内存大小
    type = models.CharField(max_length=50, blank=True, null=True)  # 类型（DDR3)
    speed = models.CharField(max_length=50, blank=True, null=True)  # 速度
    clockspeed = models.CharField(max_length=50, blank=True, null=True)  # 实际读写速度
    banklocator = models.CharField(max_length=50, blank=True, null=True)  # 内存在单板上的位置
    config = models.ForeignKey(Config)  # 配置

    class Meta:
        db_table = 'memory'


class Net(models.Model):  # 网卡
    interface = models.CharField(max_length=50, blank=True, null=True)  # 网卡接口
    bandwidth = models.CharField(max_length=50, blank=True, null=True)  # 带宽
    driver = models.CharField(max_length=50, blank=True, null=True)  # 驱动
    driverversion = models.CharField(max_length=50, blank=True, null=True)  # 驱动版本
    protocoltype = models.CharField(max_length=50, blank=True, null=True)  # 网络协议
    address = models.CharField(max_length=50, blank=True, null=True)  # 网络地址
    broadcast = models.CharField(max_length=50, blank=True, null=True)  # 子网掩码
    netmask = models.CharField(max_length=50, blank=True, null=True)  # 网关
    network = models.CharField(max_length=50, blank=True, null=True)  # 子网
    mac = models.CharField(max_length=50, blank=True, null=True)  # mac地址
    config = models.ForeignKey(Config)  # 配置

    class Meta:
        db_table = 'net'


class Storage(models.Model):  # 硬盘
    devicename = models.CharField(max_length=50, blank=True, null=True)  # 硬盘设备名称
    manufactor = models.CharField(max_length=50, blank=True, null=True)  # 制造商
    capacity = models.CharField(max_length=50, blank=True, null=True)  # 容量
    sectorsize = models.CharField(max_length=50, blank=True, null=True)  # 扇区大小
    config = models.ForeignKey(Config)  # 配置

    class Meta:
        db_table = 'storage'


class Partition(models.Model):  # 分区
    name = models.CharField(max_length=255, blank=True, null=True)  # 分区名称
    size = models.FloatField()  # 分区大小
    storage = models.ForeignKey(Storage)  # 硬盘

    class Meta:
        db_table = 'partition'


class Dimension(models.Model):  # 维度表
    name = models.CharField(max_length=50, null=False)  # 维度名称
    desc = models.CharField(max_length=200, blank=True, null=True)  # 维度描述

    class Meta:
        db_table = 'dimension'


class Scenario(models.Model):  # 场景
    name = models.CharField(max_length=50, null=False)  # 场景名称
    dim = models.ForeignKey(Dimension)  # 维度
    desc = models.CharField(max_length=200, blank=True, null=True)  # 场景描述
    parentid = models.IntegerField(default=-1)  # 父场景名称

    class Meta:
        db_table = 'scenario'


class TestTool(models.Model):
    name = models.CharField(max_length=50, null=False)  # 工具名称
    desc = models.CharField(max_length=200, blank=True, null=True)  # 工具描述

    class Meta:
        db_table = 'testTool'


class TestCase(models.Model):  # 用例表
    tool = models.ForeignKey(TestTool)  # 测试工具
    scenario = models.ForeignKey(Scenario)  # 场景
    name = models.CharField(max_length=50, null=False)  # 用例名称
    desc = models.CharField(max_length=200, blank=True, null=True)  # 用例描述

    class Meta:
        db_table = 'testCase'


class Task(models.Model):  # 测试任务
    owner = models.ForeignKey(User, related_name="owner")  # 拥有者
    config = models.ForeignKey(Config)  # 测试配置
    time = models.DateTimeField(auto_created=True)  # 上传日期
    remark = models.CharField(max_length=50, blank=True, null=True)  # 备注
    delete = models.BooleanField(default=False)  # 是否删除
    name = models.CharField(max_length=50, null=False)  # 测试任务名称
    shareusers = models.ManyToManyField(User, related_name='shareUsers')  # 共享表和用户的多对多关系

    class Meta:
        db_table = 'task'


class DimResult(models.Model):  # 维度得分
    task = models.ForeignKey(Task)  # 测试任务
    result = models.FloatField()  # 得分
    dim = models.ForeignKey(Dimension)  # 维度

    class Meta:
        db_table = 'dimResult'


class ScenarioResult(models.Model):  # 场景得分
    result = models.FloatField()  # 得分
    dimresult = models.ForeignKey(DimResult)  # 维度得分
    scenarioid = models.ForeignKey(Scenario)  # 场景

    class Meta:
        db_table = 'scenarioResult'


class CaseResult(models.Model):  # 测试用例得分
    result = models.FloatField()  # 得分
    case = models.ForeignKey(TestCase)  # 测试用例
    sceResult = models.ForeignKey(ScenarioResult)  # 场景得分
    caseconfig = models.CharField(max_length=200, blank=True, null=True)  # 执行用例的命令
    unit = models.CharField(max_length=255, blank=True, null=True)  # 单位

    class Meta:
        db_table = 'caseResult'


class Log(models.Model):  # 测试工具日志
    toolid = models.ForeignKey(TestTool)  # 测试工具
    path = models.CharField(max_length=255, null=False)  # 工具路径
    content = models.TextField(blank=True, null=True)  # 解析后的内容
    task = models.ForeignKey(Task)  # 测试任务

    class Meta:
        db_table = 'log'
