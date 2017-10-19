#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/18 17:17
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

from biz.model.models import User
from core.web.coroweb import get, post


@get('/')
async def get_index():
    users = await User.findAll()
    return {
        '__template__': 'index.html',
        'users': users
    }


@get('/{name}')
def get_name(name, **kw):
    return '<h1>hello, %s <h1/> %s' % (name, str(kw))


@post('/post/{name}')
def post_name(name, *, age, city='Hangzhou'):
    return '''<h1>hello, %s</h1>
    <h2>age: %s</h2>
    <h2>city: %s</h2>
    ''' % (name, age, city)
