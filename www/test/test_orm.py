#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/18 12:48
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0
import asyncio

import orm
from models import User


def test(loop):
    yield from orm.create_pool(loop=loop, user='www-data', password='www-data', db='awesome')

    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    yield from u.save()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
