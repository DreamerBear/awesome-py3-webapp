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


class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''

    def __init__(self, field, message=''):
        super().__init__('value:invalid', field, message)


class APIResourceNotFoundError(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''

    def __init__(self, field, message=''):
        super().__init__('value:notfound', field, message)


class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''

    def __init__(self, message=''):
        super().__init__('permission:forbidden', 'permission', message)
