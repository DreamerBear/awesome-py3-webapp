#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/18 13:34
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0
import asyncio
import functools
import inspect
import logging
import os
from urllib import parse

from aiohttp import web

from core.common.apis import APIError

logging.basicConfig(level=logging.INFO)


def get(path):
    " Define decorator @get('/path')"

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper

    return decorator


def post(path):
    "Define decorator @post('/path')"

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper

    return decorator


def get_required_named_kw_args(fn):
    '''获取必传(无默认值)的命名关键字参数名,
    在python中从*或*args到**kw中间出现的参数'''
    return get_named_kw_args(fn, False)


def get_named_kw_args(fn, has_default=None):
    '获取命名关键字参数名'
    args = []
    parameters = inspect.signature(fn).parameters
    for name, param in parameters.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            if has_default is None:
                args.append(name)
            elif not has_default and param.default == inspect.Parameter.empty:
                args.append(name)
            elif has_default and param.default != inspect.Parameter.empty:
                args.append(name)
    return tuple(args)


def has_var_kw_args(fn):
    '是否有关键字参数**kw'
    parameters = inspect.signature(fn).parameters
    for name, param in parameters.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


def has_request_arg(fn):
    sig = inspect.signature(fn)
    parameters = sig.parameters
    found = False
    for name, param in parameters.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request param must be the last named param in function: %s%s' % (fn.__name__, str(sig)))
    return found


class RequestHandler(object):
    def __init__(self, app, fn):
        self._app = app
        self._func = fn

        self._named_kw_args = get_named_kw_args(fn)
        self._required_named_kw_args = get_required_named_kw_args(fn)

        self._has_request_arg = has_request_arg(fn)
        self._has_named_kw_args = len(self._named_kw_args) > 0
        self._has_var_kw_args = has_var_kw_args(fn)

    @staticmethod
    def _putin_kw(k, v, kw: dict):
        if k in kw:
            logging.warning('Duplicate arg name: %s' % k)
        kw[k] = v

    @staticmethod
    def _merge_kw(fr, to: dict):
        for k, v in fr.items():
            RequestHandler._putin_kw(k, v, to)

    async def __call__(self, request: web.Request):
        kw = dict()
        # 有关键字参数才会从qs或post中取数据
        if self._has_var_kw_args or self._has_named_kw_args:
            # 从qs中取参数
            qs = request.query_string
            if qs:
                for k, v in parse.parse_qs(qs, True).items():
                    v = v[0] if len(v) == 1 else v
                    RequestHandler._putin_kw(k, v, kw)
            # 取post参数，覆盖qs中的同名参数，并警告
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type.')
                ct = request.content_type.lower()
                # json
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    RequestHandler._merge_kw(params, kw)
                # form
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    RequestHandler._merge_kw(params, kw)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % ct)
        # 只有命名关键字参数需要做剔除
        if not self._has_var_kw_args and self._named_kw_args:
            copy = dict()
            for name in self._named_kw_args:
                if name in kw:
                    copy[name] = kw[name]
            kw = copy
        # 取路径参数，覆盖同名参数并警告
        RequestHandler._merge_kw(request.match_info, kw)
        # 取request参数
        if self._has_request_arg:
            kw['request'] = request
        # 检查必传参数
        if self._required_named_kw_args:
            for name in self._required_named_kw_args:
                if name not in kw:
                    return web.HTTPBadRequest(reason='Missing argument: %s' % name)

        logging.info('call with args: %s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


def add_static(app: web.Application,path):
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


def add_route(app: web.Application, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info(
        'add route %s %s => %s(%s)' % (method, path, fn.__name__, ','.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))


def add_routes(app: web.Application, module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n + 1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)


if __name__ == '__main__':
    pass
