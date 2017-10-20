#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/18 17:08
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0
import asyncio
import logging.config

from aiohttp import web

import core.orm.orm as orm
from biz.controller.middlewares import auth_factory, log_factory, response_factory
from config import configs
from core.template.jinja2.init import init_jinja2
from core.web.coroweb import add_routes, add_static

# logging.config.fileConfig('conf/logging.conf')
logger = logging.getLogger('core')
log_level = configs.getValueWithDefault('log_level', logging.INFO)
logging.getLogger().setLevel(log_level)


async def init(loop: asyncio.AbstractEventLoop):
    await orm.create_pool(loop, **configs.db)
    app = web.Application(loop=loop, middlewares=[
        auth_factory, log_factory, response_factory
    ])
    init_jinja2(app)
    add_routes(app, configs.handler_module_name)
    add_static(app, configs.static_path)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', '9000')
    logger.info('server started at http://127.0.0.1:9000...')
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
