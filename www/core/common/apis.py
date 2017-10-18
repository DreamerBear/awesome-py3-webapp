#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/18 16:34
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

'''
JSON API definition
'''


class APIError(Exception):
    def __init__(self, error, data='', message=''):
        super().__init__(message)
        self.error = error
        self.data = data
        self.message = message
