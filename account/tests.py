# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import urllib2

from django.test import TestCase
from urllib import urlencode
# Create your tests here.
if __name__ == '__main__':
    server_url = "caliper.com:8001"
    server_user = "root"
    server_password = "Huawei12#$"
    url =  'http://%s/data/cert?' % (server_url) + urlencode({"username": server_user, "password": server_password})
    print url
    login_upload = urllib2.Request(url)
    response = urllib2.urlopen(login_upload).read()
    print response