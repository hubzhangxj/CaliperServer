# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
import json, os, uuid
from shared import Utils
from CaliperServer import settings
from shared.Response import Response
from django.http import HttpResponse
from shared.log import  logger


@csrf_exempt
def upload(request):
    '''
    上传数据接口，有2个文件参数，4个文本参数
    原始的数据压缩包: output
    解析过得工具日志压缩包: log
    用户名：username
    得分json：result
    原始的数据压缩包Hash值: hash_output
    解析过得工具日志压缩包:hash_log
    '''
    print "============"
    if request.method == "POST":
        print "------------------"
        if "output" in request.FILES and "log" in request.FILES:
            outputFile = request.FILES.get("output", None)
            logFile = request.FILES.get("log", None)
            # obJson = request.POST
            # params = json.loads(obJson)
            username = request.POST['username']
            result = request.POST['result']
            hash_output = request.POST['hash_output']
            hash_log = request.POST['hash_log']
            outputFileName = str(uuid.uuid1())
            logFileName = str(uuid.uuid1())
            output_path = os.path.join(settings.uploadPath, outputFileName + '.tar.gz')
            log_path = os.path.join(settings.uploadPath, logFileName + '.tar.gz')
            with open(output_path, 'wb+') as destination: #保存output 压缩包
                for chunk in outputFile.chunks():
                    destination.write(chunk)

            with open(log_path, 'wb+') as destination: #保存log 压缩包
                for chunk in logFile.chunks():
                    destination.write(chunk)

            realOutputHash = Utils.calcHash(output_path)
            realLogHash = Utils.calcHash(log_path)

            if hash_output != realOutputHash or hash_log != realLogHash: #废弃 这次任务
                os.remove(output_path)
                os.remove(log_path)
                return  HttpResponse(status=400)
            else: #存储数据库，解析文件
                logger.debug("入库操作")
        else:
            return HttpResponse(status=400)
    return HttpResponse(status=200)

def save_db():
    logger.debug("保存数据库")