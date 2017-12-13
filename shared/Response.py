#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')
from django.http import HttpResponse
import json

#user/cost/saveWarning
# def response(code,data={},type="application/json"):
#     data = {"code":code,"data":data}
#     return HttpResponse(json.dumps(data),content_type=type)
#
#



class Response:

    CODE_SUCCESS = 0 #请求成功
    CODE_FAILED = 1 #请求失败

    # @staticmethod
    # def PageResponse(code, msg, data, page, pageSize, total):
    #     objJson = {}
    #     objJson['code'] = code
    #     objJson['msg'] = msg
    #     objJson['data'] = data
    #     objJson['page'] = page
    #     objJson['pageSize'] = pageSize
    #     objJson['total'] = total
    #     objJson = json.dumps(objJson)
    #     return HttpResponse(objJson, content_type="application/json")
    @staticmethod
    def CustomJsonResponse(code,msg, data={}):
        objJson = {}
        objJson['code'] = code
        objJson['msg'] = msg
        objJson['data'] = data
        objJson = json.dumps(objJson)
        return HttpResponse(objJson, content_type="application/json")