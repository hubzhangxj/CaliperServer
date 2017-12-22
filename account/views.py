# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import StreamingHttpResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import CaliperServer.settings as settings
from shared.Response import Response
from shared.log import logger
import os, re, json
import operator
from django.contrib import auth
from account.models import UserProfile


def main(request):
    downloadPath = settings.downloadPath
    versions = []
    for path in os.listdir(downloadPath):
        if path.endswith('.zip'):
            version = re.search('v(\S+)\.', path)
            if version is not None:
                obj = {'version': version.group(1), 'path': os.path.join(downloadPath, path)}
                versions.append(obj)
    versions.sort(key=operator.itemgetter('version'), reverse=True)
    logger.debug(versions)

    data = {'versions': json.dumps(versions),"yyy":"pppp"}

    return render(request, "main.html", data)


def download(req):
    downloadPath = settings.downloadPath
    try:
        filePath = ''
        version = req.GET.get('version')
        # obJson = req.body
        # params = json.loads(obJson)
        # version = params['version']
        for path in os.listdir(downloadPath):
            if path.endswith('.zip'):
                v = re.search('v(\S+)\.', path)
                if v is not None and v.group(1) == str(version):
                    filePath = os.path.join(downloadPath, path)
                    print filePath
    except Exception as e:
        logger.error(str(e))
        return Response.CustomJsonResponse(Response.CODE_FAILED, 'fail')
    if filePath is not None:
        splits = filePath.split("/")
        fileName = splits[len(splits) - 1]
        response = StreamingHttpResponse(file_iterator(filePath))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(fileName)
        return response

def file_iterator(filename, chunk_size=512):
    with open(filename, "rb") as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break

def login(req):
    user = UserProfile.objects.get(username="max")
    auth.login(req, user)
    return HttpResponseRedirect("/task/list")
