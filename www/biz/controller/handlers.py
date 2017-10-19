#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/18 17:17
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

from biz.model.models import User,Blog,Comment
from core.web.coroweb import get, post
import time

@get('/')
async def get_index():
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time() - 120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time() - 3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time() - 7200)
    ]
    return {
        '__template__': 'index.html',
        'blogs': blogs
    }

