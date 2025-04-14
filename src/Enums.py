# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import os
import getpass
from enum import StrEnum


class HttpUserAgent(StrEnum):
    ANDROID_FIREFOX = "Mozilla/5.0 (Android 10; Mobile; rv:89.0) Gecko/89.0 Firefox/89.0"  # fmt: skip
    ANDROID_LINUX = "Mozilla/5.0 (Linux; Android 9; ASUS_X00TD; Flow) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/359.0.0.288 Mobile Safari/537.36"
    ANDROID_WECHAT = "Mozilla/5.0 (Linux; Android 13; PFCM00 Build/TP1A.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.103 Mobile Safari/537.36 XWEB/1300467 MMWEBSDK/20241202 MMWEBID/4691 MicroMessenger/8.0.56.2800(0x2800385E) WeChat/arm64 Weixin NetType/5G Language/zh_CN ABI/arm64"
    IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
    LINUX_FIREFOX = "Mozilla/5.0 (X11; Linux i686; rv:114.0) Gecko/20100101 Firefox/114.0"  # fmt: skip
    MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    WINDOWS_CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.1052.53 Safari/537.36"
    WINDOWS_EDGE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0"
    WINDOWS_FIREFOX = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0"
    WINDOWS_LENOVO = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SLBrowser/9.0.6.2081 SLBChan/8 SLBVPV/64-bit"

    @classmethod
    def generate_user_agent(cls):
        rand = hash((getpass.getuser(), os.getcwd())) % len(cls._member_map_)
        return cls._member_map_[list(cls._member_map_.keys())[rand]]


class QiangGuoXianFengBaseURL(StrEnum):
    USTB_GFJY = "https://gfjy.ustb.edu.cn"
    USTB_DXPX = "https://dxpx.ustb.edu.cn"

    @classmethod
    def all_names(cls):
        return cls._member_names_

    @classmethod
    def contains_name(cls, name):
        return any(member_name == name.upper() for member_name in cls._member_names_)

    @classmethod
    def of_name(cls, name):
        return cls._member_map_[name.upper()]
