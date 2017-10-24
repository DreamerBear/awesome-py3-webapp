#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017/10/17 16:14
# @Author  : xxc727xxc (xxc727xxc@foxmail.com)
# @Version : 1.0.0

import asyncio
import functools
import logging

import aiomysql
from werkzeug import local

logger = logging.getLogger(__name__)
conn_local = local.Local()


def log(sql, args=()):
    logger.debug('SQL: %s  args: %s' % (sql, args))


def get_transaction():
    return _DBTransaction(__pool)


@asyncio.coroutine
def create_pool(loop: asyncio.AbstractEventLoop, **kw):
    logger.info('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', False),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


class _DBTransaction(object):
    'transaction contextmanager based on werkzeug.local'

    def __init__(self, pool):
        self.pool = pool
        self.isNested = False

    async def __aenter__(self):
        if getattr(conn_local, 'cursor', None) is None:
            self.conn = await self.pool.acquire()
            self.cursor = await self.conn.cursor()
            if self.conn.get_autocommit():
                await self.conn.autocommit(False)
                logger.debug('close autocommit for current connection')
            conn_local.conn = self.conn
            conn_local.cursor = self.cursor
            await self.conn.begin()
            logger.debug('transaction begin')
        else:
            self.isNested = True
            self.conn = conn_local.conn
            self.cursor = conn_local.cursor
        return self.cursor

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if not self.isNested:
                if exc_type is not None:
                    await self.conn.rollback()
                    logger.debug('transaction rollback')
                try:
                    await self.conn.commit()
                    logger.debug('transaction commit')
                except BaseException:
                    await self.conn.rollback()
                    logger.debug('transaction rollback')
                    raise
                finally:
                    await self.cursor.close()
                    self.pool.release(self.conn)
                    local.release_local(conn_local)
                    logger.debug('cursor close and connection release')
        finally:
            self.conn = None
            self.cursor = None


def transaction(func):
    if not asyncio.iscoroutinefunction(func):
        raise TypeError('transaction decorator can only apply on async function')

    @functools.wraps(func)
    async def wrapper(*args, **kw):
        async with get_transaction():
            return await func(*args, **kw)

    return wrapper


@asyncio.coroutine
def select(sql, args, size=None):
    log(sql, args)
    global __pool
    cur = getattr(conn_local, 'cursor', None)
    if cur is None:
        with (yield from __pool) as conn:
            cur = yield from conn.cursor(aiomysql.DictCursor)
            yield from cur.execute(sql.replace('?', '%s'), args or ())
            rs = yield from fetchRs(cur, size)
            yield from cur.close()
            logger.debug('rows return: %s' % str(rs))
            return rs
    else:
        yield from cur.execute(sql.replace('?', '%s'), args or ())
        rs = yield from fetchRs(cur, size)
        logger.debug('rows return: %s' % str(rs))
        return rs


@asyncio.coroutine
def fetchRs(cur: aiomysql.Cursor, size):
    if size:
        rs = yield from cur.fetchmany(size)
    else:
        rs = yield from cur.fetchall()
    return rs


async def execute(sql, args):
    log(sql, args)
    cursor = getattr(conn_local, 'cursor', None)
    if not cursor:
        async with get_transaction() as cur:
            await cur.execute(sql.replace('?', '%s'), args)
            return cur.rowcount
    else:
        await cursor.execute(sql.replace('?', '%s'), args)
        return cursor.rowcount


class Field(object):
    def __init__(self, column_name, column_type, primary_key, default):
        self.column_name = column_name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.column_name)


class StringField(Field):
    def __init__(self, column_name=None, column_type='varchar(100)', primary_key=False, default=None):
        super().__init__(column_name, column_type, primary_key, default)


class BooleanField(Field):
    def __init__(self, column_name=None, default=False):
        super().__init__(column_name, 'boolean', False, default)


class IntegerField(Field):
    def __init__(self, column_name=None, primary_key=False, default=0):
        super().__init__(column_name, 'bigint', primary_key, default)


class FloatField(Field):
    def __init__(self, column_name=None, primary_key=False, default=0.0):
        super().__init__(column_name, 'real', primary_key, default)


class TextField(Field):
    def __init__(self, column_name=None, default=None):
        super().__init__(column_name, 'text', False, default)


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # 排除Model类本身
        if name == 'Model':
            return super().__new__(cls, name, bases, attrs)
        # 获取table名称
        tableName = attrs.get('__table__', None) or name
        logger.debug('fond model ; %s (table: %s)' % (name, tableName))
        # 获取所有的Field和主键名
        prop_column_mappings = dict()
        column_prop_mappings = dict()
        fields = list()
        primaryColumn = None
        primaryKey = None

        for k, v in attrs.items():
            if isinstance(v, Field):
                logger.debug('  found mapping: %s ==> %s' % (k, v))
                prop_column_mappings[k] = v
                if v.column_name:
                    column_prop_mappings[v.column_name] = k
                else:
                    column_prop_mappings[k] = k
                if v.primary_key:
                    if primaryColumn:
                        raise RuntimeError('Duplicate primary key for (%s,%s)' % (primaryColumn, k))
                    primaryColumn = v.column_name or k
                    primaryKey = k
                else:
                    fields.append(k)

        if not primaryColumn:
            raise RuntimeError('Primary key not found')
        for k in prop_column_mappings.keys():
            attrs.pop(k)

        escaped_colums_with_separator = ','.join(
            list(map(lambda f: '`%s`' % (prop_column_mappings[f].column_name or f), fields)))
        attrs['__mappings__'] = prop_column_mappings  # 保存属性和列的映射关系
        attrs['__column_prop_mappings__'] = column_prop_mappings  # 保存列到属性名的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey  # 主键属性名
        attrs['__primary_column__'] = primaryColumn  # 主键列名
        attrs['__fields__'] = fields  # 除主键外的属性名
        # 构造默认的CRUD语句
        attrs['__select__'] = 'select `%s`,%s from `%s`' % (primaryColumn, escaped_colums_with_separator, tableName)
        attrs['__insert__'] = 'insert into `%s` (%s,`%s`) values (%s)' % (
            tableName, escaped_colums_with_separator, primaryColumn, ('?,' * (len(fields) + 1))[0:-1])
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
            tableName, ','.join(map(lambda f: '`%s`=?' % (prop_column_mappings[f].column_name or f), fields)),
            primaryColumn)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryColumn)

        return super().__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super().__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Modal' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def __str__(self):
        return '<%s> %s' % (self.__class__.__name__, super().__str__())

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = self.getValue(key)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logger.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    def __build_res(cls, rs):
        column_prop_mappings = cls.__column_prop_mappings__
        kw = dict()
        for k, v in rs.items():
            kw[column_prop_mappings[k]] = v
        return kw

    @classmethod
    @asyncio.coroutine
    def findAll(cls, where=None, args=None, **kw):
        'find objects by where clause'
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        args = args or []
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = yield from select(' '.join(sql), args)
        return [cls(**(cls.__build_res(r))) for r in rs]

    @classmethod
    @asyncio.coroutine
    def count(cls, select_column, where=None, args=None):
        'find number by select and where'
        sql = ['select count(%s) as num from `%s`' % (select_column, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = yield from select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['num']

    @classmethod
    @asyncio.coroutine
    def find(cls, pk):
        ' find object by primary key'
        rs = yield from select('%s where `%s`=?' % (cls.__select__, cls.__primary_column__), (pk,), 1)
        if len(rs) == 0:
            return None
        return cls(**cls.__build_res(rs[0]))

    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__, args)
        if rows != 1:
            logger.warning('failed to insert record: affected rows: %s' % rows)

    @asyncio.coroutine
    def update(self, **kw):
        for k, v in kw.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise AttributeError(r"'Modal' object has no attribute '%s'" % k)
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__update__, args)
        if rows != 1:
            logger.warning('failed to update record: affected rows: %s' % rows)

    @asyncio.coroutine
    def remove(self):
        args = [self.getValueOrDefault(self.__primary_key__)]
        rows = yield from execute(self.__delete__, args)
        if rows != 1:
            logger.warning('failed to remove record: affected rows: %s' % rows)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_pool(loop, user='root', password='root', db='test'))


    class User(Model):
        __table__ = 'user'
        id = StringField(column_type='varchar(20)', primary_key=True)
        sname = StringField('name', 'varchar(20)')


    async def asy_print(f, delay=0):
        await asyncio.sleep(delay)
        print(await f)


    user = User(id='6', sname='beta')
    tasks = [
        asyncio.ensure_future(asy_print(User.count('id'))),
        asyncio.ensure_future(asy_print(User.find('1'))),
        asyncio.ensure_future(asy_print(User.findAll(where='binary name = ?', args=('bear',), orderBy='id desc'))),
        asyncio.ensure_future(asy_print(user.save())),
        asyncio.ensure_future(asy_print(user.update(sname='消息称'), 2)),
        asyncio.ensure_future(asy_print(user.remove(), 5)),
    ]

    loop.run_until_complete(asyncio.gather(*tasks))
