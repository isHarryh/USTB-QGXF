# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import base64
import re
import urllib.parse
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from io import BytesIO
from PIL import Image

_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3R7TsLurEeey4H8b002x
BTMUqFKfeNc8kK7Yy64E6YLQ1hIwTLyAstLz6x59thxFyAyemV7+Ioqarj2J6IM4
W12yshJa3hhz4yigbowBFjb1+Ib+TK0223Mzf/FMT3NvnnY4cBFPip8tsLEWwchw
9QVhBnzygijMFsTXrLIQRSvqCiAszhR9OPLI3TwN0WuEa9vXcp3yEvGw1kHWbDaB
P02oRGZyqbzJLSQdQFTV6Qh1y/6MeYsPn3munaV0fE7PhhtwwJswiPy+bSSLVIll
E0QeYMgiFCuwvC6m3h/Fm3ebGcDo7ei85y4SCcn1lJDFyS7ohTBEwG0Ny6ewNwG9
FwIDAQAB
-----END PUBLIC KEY-----"""
_ENCODING = 'UTF-8'

_CIPHER = PKCS1_v1_5.new(RSA.import_key(_PUBLIC_KEY))

def rsa_encrypt(data:str):
    encrypted = _CIPHER.encrypt(data.encode(_ENCODING))
    string = base64.b64encode(encrypted).decode(_ENCODING)
    return urllib.parse.quote(string)
