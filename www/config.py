#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/19 10:14
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

import logging

import conf.config_default as config_default

logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger('core')

class Dict(dict):
    '''
    simple dict but support access as x.y style.
    '''

    def __init__(self, names=(), values=(), **kw):
        super().__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'dict' object has no attribute: %s" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValueWithDefault(self, key, default=None):
        return self[key] if hasattr(self, key) else default


def toDict(d: dict):
    copy = Dict()
    for k, v in d.items():
        copy[k] = toDict(v) if isinstance(v, dict) else v
    return copy


def override_dict(default: dict, override: dict):
    r = {}
    for k, v in default.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = override_dict(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    for k, v in override.items():
        if k not in default:
            r[k] = v
    return r


configs = config_default.configs

try:
    import conf.config_override as config_override

    configs = override_dict(configs, config_override.configs)
except ImportError:
    logger.warning('config_override not found')
    pass

configs = toDict(configs)

if __name__ == '__main__':
    print(configs)
