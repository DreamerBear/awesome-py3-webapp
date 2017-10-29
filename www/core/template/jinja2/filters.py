#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/19 12:52
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

from datetime import datetime
import time

from core.template.jinja2.init import jinja_filter


@jinja_filter('datetime')
def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return '1分钟前'
    if delta < 3600:
        return '%s分钟前' % (delta // 60)
    if delta < 86400:
        return '%s小时前' % (delta // 3600)
    if delta < 604800:
        return '%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return '%s年%s月%s日' % (dt.year, dt.month, dt.day)
