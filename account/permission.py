#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

from django.shortcuts import render, HttpResponseRedirect

def login_required(fun):
    """
    检查登录装饰器，如果没有登录就渲染unlogin界面
    """
    def wapper(request, *args, **kwargs):
        if request.user is None or request.user.is_anonymous():
            return HttpResponseRedirect('/')

        return fun(request, *args, **kwargs)
    return wapper