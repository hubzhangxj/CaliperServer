#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

from django.shortcuts import HttpResponseRedirect
from django.contrib import auth
from .sso import logined_users


def login_required(fun):
    """
    检查是否登录
    :param fun:
    :return:
    """
    def wapper(request, *args, **kwargs):
        auth_token_session = request.session.get("auth_token", None)
        if not auth_token_session:
            print "auth_token not exist"
            if request.user and not request.user.is_anonymous():  # 登录用户
                auth.logout(request)
            return HttpResponseRedirect('/')
        else:
            if auth_token_session not in logined_users.keys():
                auth.logout(request)
                return HttpResponseRedirect('/')
            else:
                if request.user is None or request.user.is_anonymous():  # 未登录用户
                    return HttpResponseRedirect('/')
                else:  # 已登录用户
                    return fun(request, *args, **kwargs)
    return wapper

