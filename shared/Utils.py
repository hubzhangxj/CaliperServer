# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from shared.serializers.json import Serializer
from django.http import HttpResponse
import json
import requests
import re
from datetime import datetime
import os
from Crypto.PublicKey import RSA
from users import models as userModels
from login import models as loginModels
from Estuary import settings
import tarfile,zipfile
import uuid
import logging


def ChoiceToDic(choice):
    """Choice(tuple)转换成字典"""
    dic = {}
    for c in choice:
        dic[c[0]] = c[1]
    return dic


def JsonResponse(code, msg, items="", total=-1):
    """接口响应封装类"""
    objJson = {}
    objJson['code'] = code
    objJson['msg'] = msg
    if items != "":
        objJson['items'] = Serializer().serialize(items)
    if total != -1:
        objJson['total'] = total
    objJson = json.dumps(objJson)
    objJson = objJson.replace('": "[', '": [').replace(']", "', '], "').decode("unicode-escape")
    return HttpResponse(objJson, content_type="application/json")


def CustomJsonResponse(code, msg, items, total):
    """接口响应封装类"""
    objJson = {}
    objJson['code'] = code
    objJson['msg'] = msg
    objJson['items'] = items
    objJson['total'] = total
    objJson = json.dumps(objJson)
    objJson = objJson.replace('": "[', '": [').replace(']", "', '], "').decode("unicode-escape")
    return HttpResponse(objJson, content_type="application/json")

def getip():
    try:
        myip, myloc = taobao("http://ip.taobao.com/service/getIpInfo2.php?ip=myip")

    except:
        try:
            myip, myloc = chinaz("http://ip.chinaz.com/getip.aspx")
        except:
            try:

                myip, myloc = sohu("http://pv.sohu.com/cityjson?ie=utf-8")  # visit访问节点
            except:
                myip, myloc = 0, None

    return myip, myloc


def chinaz(url):
    response = requests.get(url)
    ipaddr = re.search("ip:'([\s\S]+?)'", response.text).groups()[0]
    location = re.search("address:'([\s\S]+?)'", response.text).groups()[0]
    return ipaddr, location


def taobao(url):
    response = requests.get(url)
    jsonObj = json.loads(response.text)
    ipaddr = jsonObj["data"]["ip"]
    location = jsonObj["data"]["region"] + jsonObj["data"]["city"] + jsonObj["data"]["isp"]

    return ipaddr, location


def sohu(url):
    response = requests.get(url)
    jsonstr = re.search('=\s{1,}([\s\S]+?);', response.text).groups()[0]
    jsonObj = json.loads(jsonstr)
    ipaddr = jsonObj["cip"]
    location = jsonObj["cname"]

    return ipaddr, location


def isPhone(value):
    p2 = re.compile('^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}')
    phonematch = p2.match(value)

    return phonematch

def enum2Json(value):
    """
    将枚举转换成json 字符串
    :param value:
    :return:
    """
    out = []
    for v in value:
        obj = {}
        obj['key'] = v.name
        obj['value'] = v.value
        out.append(obj)
    j = json.dumps(out).decode("unicode-escape")
    return j


def byteify(input):
    '''
    转换 dict 里的unicode
    :param input:
    :return:
    '''
    if isinstance(input, dict):
        return {byteify(key): byteify(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

#把datetime转成字符串
def datetime_toString(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

#把字符串转成datetime
def string_toDatetime(string):
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")



def gen_key(userId,keyName):
    try:
        key = RSA.generate(2048)
        path = os.path.join(settings.MEDIA_ROOT, 'key')
        if not os.path.exists(path):
            os.mkdir(path)
        priv_key = os.path.join(path, 'priv_'+keyName+'.key')
        pub_key = os.path.join(path, 'pub_'+keyName+'.key')
        with open(priv_key, 'w') as content_file:
            content_file.write(key.exportKey('PEM'))
        pubkey = key.publickey()
        with open(pub_key, 'w') as content_file:
            content_file.write(pubkey.exportKey('OpenSSH'))
        owner = loginModels.UserProfile.objects.get(id=userId)
        tarFilePath = zip_key(priv_key, pub_key)
        ssh = userModels.SshKey(keyName=keyName,owner= owner,publicKey=pubkey.exportKey('OpenSSH'),files=tarFilePath)
        ssh.save()
    except Exception as ex:
        logging.error(str(ex))
        return None
    return os.path.join(settings.MEDIA_URL,tarFilePath)

def make_targz(output_filename, *files):
    tar = tarfile.open(output_filename, "w:gz")
    for f in files:
        tar.add(f,arcname=os.path.basename(f)) #压缩包内去掉全路径
    tar.close()
    for f in files: #删除原始的key文件
        os.remove(f)


def zip_key(*files):
    '''
    打包key
    :param files:  全路径
    :return:
    '''
    path = os.path.join(settings.MEDIA_ROOT, 'key')
    if not os.path.exists(path):
        os.mkdir(path)
    fileName = str(uuid.uuid1()) +".tar.gz"
    output_filename = os.path.join(path,fileName)
    make_targz(output_filename,*files)
    return  "key/" + fileName


# 将连接对象中的所有数据转化为数组
def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


