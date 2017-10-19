#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/19 13:03
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0


def find_module(module_name: str):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n + 1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    return mod
