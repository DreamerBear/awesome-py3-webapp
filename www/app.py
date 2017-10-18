#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/18 17:08
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0
import asyncio
import logging
import os

from aiohttp import web

from core.web.coroweb import add_routes, add_static

logging.basicConfig(level=logging.INFO)

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


async def response_factory(app, handler):
    async def response(request):
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        # default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/html;charset=utf-8'
        return resp

    return response


async def init(loop: asyncio.AbstractEventLoop):
    app = web.Application(loop=loop, middlewares=[
        response_factory
    ])
    add_routes(app, 'biz.controller.handlers')
    add_static(app, os.path.join(BASE_PATH, 'static'))
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', '9000')
    logging.info('server started at http://127.0.0.1:9000...')
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
