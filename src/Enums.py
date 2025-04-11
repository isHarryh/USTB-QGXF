# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
from enum import StrEnum


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
