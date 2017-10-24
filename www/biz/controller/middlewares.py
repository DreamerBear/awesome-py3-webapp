#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/19 15:29
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

import json
import logging

from aiohttp import web

from biz.controller.handlers import COOKIE_NAME, cookie2user

logger = logging.getLogger(__name__)


def is_exclude(request: web.Request):
    return request.path.startswith('/static/') or request.path in ['/favicon.ico']


async def auth_factory(app, handler):
    ' aiohttp middlewares  鉴权'

    async def auth(request: web.Request):
        logger.debug('check user: %s %s' % (request.method, request.path))
        if is_exclude(request):
            return await handler(request)
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = await cookie2user(cookie_str)
            if user:
                logger.debug('set current user: %s' % user.email)
                request.__user__ = user
        if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
            logger.info(str(request.__user__))
            return web.HTTPFound('/signin')
        return await handler(request)

    return auth


async def log_factory(app, handler):
    'aiohttp middlewares log'

    async def log(request: web.Request):
        if not is_exclude(request):
            user_email = getattr(request.__user__, 'email', None)
            logger.info('Request %s %s user: %s' % (request.method, request.path_qs, user_email))
        return await handler(request)

    return log


async def response_factory(app, handler):
    ' aiohttp middlewares  将handler的返回结果格式化为Response'

    async def response(request: web.Request):
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode())
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode())
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r['__user__'] = request.__user__
                resp = web.Response(body=app['__template_engine__'].get_template(template).render(**r).encode())
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp

    return response
