#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/19 11:43
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

import functools
import logging

from jinja2 import Environment, FileSystemLoader

import core.common.utils as utils
from config import configs, Dict

options = Dict(
    autoescape=True,
    block_start_string='{%',
    block_end_string='%}',
    variable_start_string='{{',
    variable_end_string='}}',
    auto_reload=True,
)


def jinja_filter(filter_name):
    if not isinstance(filter_name, str) or len(filter_name) <= 0:
        raise ValueError('jinja_filter not named')

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__filter_name__ = filter_name
        return wrapper

    return decorator


def add_filters(env: Environment, module_name):
    mod = utils.find_module(module_name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            filter_name = getattr(fn, '__filter_name__', None)
            if filter_name:
                logging.debug('jinja2 add filter: %s' % filter_name)
                env.filters[filter_name] = fn


def init_jinja2(app):
    logging.info('init jinja2...')
    logging.debug('set jinja2 template path: %s' % configs.templates_path)
    env = Environment(loader=FileSystemLoader(configs.templates_path), **options)
    add_filters(env, configs.jinja_filters_module_name)
    app['__template_engine__'] = env
