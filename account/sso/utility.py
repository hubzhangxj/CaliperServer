# -*- coding: utf-8 -*-
from django.http import HttpResponse


def form_redirect(action, **kwargs):
    """
    以表单（静默生成一个表单并自动提交到目标action）post提交的方式代替HttpResponseRedirect,
    解决暴露字段在url上的问题。Note：这就要求action处理函数的method能接收POST
    :param action: 目标地址（重定向地址）
    :param kwargs:键值对
    """
    resp = '<script type="text/javascript">'
    resp += 'document.write(\'<form id="form_redirect" method="post" action="' + action + '">\');'
    for (key, arg) in kwargs.items():
        resp += 'document.write(\'<input type="hidden" name="'+key+'" value="' + arg + '">\');'

    resp += 'document.write("</form>");document.getElementById("form_redirect").submit();</script>'

    return HttpResponse(resp)


