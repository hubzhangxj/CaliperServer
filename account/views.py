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

from django.views.decorators.csrf import csrf_exempt
from account.permission import login_required

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
    user = UserProfile.objects.get(username="admin")
    auth.login(req, user)
    return HttpResponseRedirect("/task/list")

def logout(req):
    auth.logout(req)
    return HttpResponseRedirect('/')

@login_required
def getuserinfo(req):
    # username=req.GET.get('username')
    # if not username :
    #     return HttpResponse(status=500,content='传参数非法')
    # try:
    #     item=UserProfile.objects.get(username=username)
    #     data = {'username': item.name, 'add': item.address, 'time': item.date_joined, 'mail': item.email, \
    #             'userid': item.username, 'org': item.company, 'role': item.role, 'phone': item.telphone,
    #             'last_login': item.last_login,'avatar':item.avatar}
    # except:
    #     return HttpResponse(status=404, content='未找到')

    #return HttpResponse(status=200)
    return render(req,"userinfo.html",{'isShowBack':True})

@login_required
@csrf_exempt
def setuserinfo(req):
    if req.method == 'POST':
        data = req.POST
        username = data.get('username')
        username_file=req.GET.get('username')
        if username:
            mail = data.get('mail')
            phone = data.get('phone')
            if mail:
                try:
                    item = UserProfile.objects.get(username=username)
                except:
                    return HttpResponse(status=500, content='database connect failed')
                item.email = mail
                item.save()
                return HttpResponse(status=200)
            if phone:
                try:
                    item = UserProfile.objects.get(username=username)
                except:
                    return HttpResponse(status=500, content='database connect failed')
                item.telphone = phone
                item.save()
                return HttpResponse(status=200)
        elif   username_file:
            try:
                file=req.FILES['file']
                #filename=str(file)
            except Exception as e:
                return HttpResponse(status=500, content='unknow error')

            try:
                item = UserProfile.objects.get(username=req.user.username)
            except:
                return HttpResponse(status=500, content='database connect failed')
            item.avatar = file
            item.save()
            return HttpResponse(status=200)
      #      path = '/tmp/photo/'
         ##   if not os.path.exists(path):
         #       os.makedirs(path)
         #   with open(path +username_file+'_'+filename, 'wb+') as destination:
          #      for chunk in file.chunks():
           #         destination.write(chunk)

    else:
        return HttpResponse(status=403,content='forbidden')

@login_required
@csrf_exempt
def upload(req):
    try:
        file = req.FILES['file']
        # filename=str(file)
        item = UserProfile.objects.get(username=req.user.username)
    except:
        return HttpResponse(status=500, content='database connect failed')
    item.avatar = file
    item.save()
    return HttpResponse(status=200)