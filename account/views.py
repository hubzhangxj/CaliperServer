# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from shared.log import logger


def main(request):
    return render(request, "main.html")
