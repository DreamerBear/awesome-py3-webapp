#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/19 10:30
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

'''
default configs used in dev environment
'''
import logging

configs = {
    "log_level": logging.DEBUG,
    "db": {
        "host": "localhost",
        "port": 3306,
        "user": "www-data",
        "password": "www-data",
        "db": "awesome"
    }
}
