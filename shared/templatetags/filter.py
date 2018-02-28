#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import re
from django import template

reload(sys)
sys.setdefaultencoding('utf8')

register = template.Library()


@register.filter
def pcut(value):
    content = str(value)
    print content
    try:
        out = re.sub("\d{4}(?=[\d]{4}$)", "****", content)
    except:
        return value
    return out

@register.filter
def safen(value):
    v = str(value)
    if v is None or v == 'None':
        return ''
    else:
        return value

if __name__ == '__main__':
    print  pcut(18913387696)
