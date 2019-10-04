#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys


class MkdirError(Exception):
    pass


def mkdir(dirname):
    if os.path.exists(dirname):
        return
    try:
        os.mkdir(dirname)
    except BaseException as err:
        raise MkdirError(str(err))


def rmdir(dirname):
    if dirname[-1] == os.sep:
        dirname = dirname[:-1]
    if os.path.islink(dirname):
        return  # do not clear link - we can get out of dir
    for f in os.listdir(dirname):
        if f in ('.', '..'):
            continue
        path = dirname + os.sep + f
        if os.path.isdir(path):
            rmdir(path)
        else:
            os.unlink(path)
    os.rmdir(dirname)


def dexor(text, key):
    ret = list(text)
    mod = len(key)
    for index, char in enumerate(ret):
        ret[index] = chr(char ^ ord(key[index % mod]))
    return "".join(ret)


def die(exitMessage, exitCode=1):
    print(exitMessage)
    sys.exit(exitCode)
