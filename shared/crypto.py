#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,base64
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from CaliperServer.settings import BASE_DIR
reload(sys)
sys.setdefaultencoding('utf8')

private_url = os.path.join(BASE_DIR,'CaliperServer','master-private.pem')
public_url = os.path.join(BASE_DIR,'CaliperServer','master-public.pem')


def decrypt(encrypt_text):
    '''
    私钥解密
    :param encrypt_text:
    :return:
    '''
    text = ''
    # 伪随机数生成器
    random_generator = Random.new().read
    with open(private_url) as f:
        key = f.read()
        rsakey = RSA.importKey(key)
        cipher = Cipher_pkcs1_v1_5.new(rsakey)
        text = cipher.decrypt(base64.b64decode(encrypt_text), random_generator)
    return text

def encrypt(text):
    '''
    公钥加密
    :param text:
    :return:
    '''
    with open(public_url) as f:
        key = f.read()
        rsakey = RSA.importKey(key)
        cipher = Cipher_pkcs1_v1_5.new(rsakey)
        text = base64.b64encode(cipher.encrypt(text))
    return text

def sign(text):
    '''
    私钥签名
    :param text:
    :return:
    '''
    sign_text = ''
    text = str(text)
    with open(private_url) as f:
        key = f.read()
        rsakey = RSA.importKey(key)
        random_generator = Random.new().read
        sign_text = rsakey.sign(text, random_generator)
        sign_text = str(sign_text[0])
        sign_text = base64.b64encode(sign_text)
    return sign_text

def verify(message,sign_text):
    '''
    公钥验签
    :param text:
    :return:
    '''
    isOk = False
    sign_text = str(sign_text)
    with open(public_url) as f:
        key = f.read()
        rsakey = RSA.importKey(key)
        sign_text = base64.b64decode(sign_text)
        sign_text = (long(sign_text),)
        isOk = rsakey.verify(str(message), sign_text)
    return isOk


sign_text="OTcyODc4Njg0NTU3NjI1MzQyMzc0OTUxNjE3NDI1NDg4NjYxNTYwNTA1MzkyMTg1OTQ2MTg5NjUyMTA4MjkxMTA4MzkwMjYzNjI0MzU4Njk4ODYzNTYzMDM4OTg4MDU4MjQ5MzIzNDk0NjEwMzUyOTY5OTA4Njk3MjYxOTQ2OTY3NDY3OTc2OTQxODEzOTI3OTM0ODY1NDEzOTE0MjQ4MDM0MTA1NDE1NjY5ODA1MjY4NjY2MTM2NDcyMjc4MDAxNTc5NTYzNjA3Njk0MzczODkzMjI3ODA2MTU5NzI3Nzk3NDA2MTE4ODY0MTI5ODE4ODQ3NTQ3ODU2NDk0MjE0MzU5MzU4MjA0NjU2NTEzMzkzMzA2ODg5ODM5OTY4NzM2MzgzMzM3NTI3NjYxOTAyNzc1NTk="
if __name__ == '__main__':
    print  verify('qqq5',sign_text)



