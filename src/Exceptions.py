# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License

class InvalidRequestError(Exception):
    def __init__(self, *args):
        super().__init__(args)

class PermissionError(Exception):
    def __init__(self, *args):
        super().__init__(args)

class UnauthorizedError(Exception):
    def __init__(self, *args):
        super().__init__(args)
