#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from shared.log import logger

reload(sys)
sys.setdefaultencoding('utf8')

try:
    from django.utils.deprecation import MiddlewareMixin  # Django 1.10.x
except ImportError:
    MiddlewareMixin = object  # Django 1.4.x - Django 1.9.x


class ExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        try:
            logger.debug("---------- HTTP  Error Msg ---------- ")
            logger.debug(exception)
            import traceback
            logger.debug(traceback.format_exc())
            logger.debug("---------------------------------------- ")
        except Exception:
            pass
        return None
