# -*- coding: utf-8 -*-
import urllib
from . import REMOTE_AUTH_TOKEN_URL
from apiclient import client
from account.models import UserProfile


class SSOAuthBackend(object):
    @staticmethod
    def authenticate(auth_token):
        try:
            code, user_info = client.send_request(
                REMOTE_AUTH_TOKEN_URL + "?" + urllib.urlencode({"auth_token": auth_token}))

            return None, UserProfile.objects.filter(username=user_info["username"]).first(), user_info
        except Exception as e:
            print e.message
            return e.message, None, None

    def get_user(self, uid):
        try:
            user = UserProfile.objects.get(id=uid)
            return user
        except Exception as e:
            print e.message
            return None
