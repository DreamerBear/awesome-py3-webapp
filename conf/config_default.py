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

import www.static as static
import www.templates as templates

configs = {
    "templates_path": os.path.dirname(os.path.abspath(templates.__file__)),
    "static_path": os.path.dirname(os.path.abspath(static.__file__)),
    'handler_module_name': 'www.biz.controller.handlers',
    'jinja_filters_module_name': 'www.core.template.jinja2.filters',
    "log_level": logging.DEBUG,
    "db": {
        "host": "localhost",
        "port": 3306,
        "user": "www-data",
        "password": "www-data",
        "db": "awesome"
    }
}
