#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/19 10:30
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

'''
default configs used in dev environment
'''
import logging
import os

configs = {
    "templates_path": os.path.join(os.path.abspath('.'), 'templates'),
    "static_path": os.path.join(os.path.abspath('.'), 'static'),
    'handler_module_name': 'biz.controller.handlers',
    'jinja_filters_module_name': 'core.template.jinja2.filters',
    "log_level": logging.DEBUG,
    "db": {
        "host": "localhost",
        "port": 3306,
        "user": "www-data",
        "password": "www-data",
        "db": "awesome"
    },
    "session": {
        "secret": "awesome",
        "name": "apw-session"
    }
}
