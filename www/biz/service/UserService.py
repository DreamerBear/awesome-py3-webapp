#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/20 17:42
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

import asyncio
import hashlib
import logging
import re

import core.orm.orm as orm
from biz.model.models import User, next_id
from config import configs
from core.common.apis import APIError, APIValueError


class UserService(object):
    _RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
    _RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

    @classmethod
    async def newUser(cls, email, passwd, name):
        if not name or not name.strip():
            raise APIValueError('name')
        if not email or not cls._RE_EMAIL.match(email):
            raise APIValueError('email')
        if not passwd or not cls._RE_SHA1.match(passwd):
            raise APIValueError('passwd')
        users = await User.findAll('email=?', [email])
        if len(users) > 0:
            raise APIError('register:failed', 'email', 'Email is already in use.')
        uid = next_id()
        sha1_passwd = '%s:%s' % (uid, passwd)
        user = User(id=uid, name=name.strip(), email=email,
                    passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                    image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(
                        email.encode('utf-8')).hexdigest())
        return user

    @classmethod
    async def makeAdmin(cls, users: tuple):
        async with orm.get_transaction() as cursor:
            for user in users:
                if not isinstance(user, User):
                    raise ValueError('type must be user')
                users = await User.findAll('email=?', [user.email])
                if len(users) > 0:
                    await user.update(admin=True, cursor=cursor)
                else:
                    user.admin = True
                    await user.save(cursor=cursor)

    @classmethod
    def makePasswd(cls, email, passwd):
        return hashlib.sha1((email + ':' + passwd).encode()).hexdigest()


if __name__ == '__main__':
    # CryptoJS.SHA1('admin1@123.com' + ':' + '123456').toString()
    logging.basicConfig(level=logging.debug)


    async def init_db(loop: asyncio.AbstractEventLoop):
        await orm.create_pool(loop, **configs.db)


    async def test():
        admin1 = await UserService.newUser('admin1@123.com', UserService.makePasswd('admin1@123.com', '123456'),
                                           'admin1')
        admin2 = await UserService.newUser('admin2@123.com', UserService.makePasswd('admin2@123.com', '123456'),
                                           'admin1')
        admin3 = 'bug'
        await UserService.makeAdmin((admin1, admin2, admin3))


    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db(loop))
    loop.run_until_complete(test())
