#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import string

def load_file(filename):
    if filename == "-":
        return sys.stdin.read()
    fd = open(filename, "rb")
    contents = fd.read()
    fd.close()
    return contents


def save_file(filename, data):
    fd = open(filename, "wb")
    fd.write(data)
    fd.close()
    return


def mkdir(dirname):
    if os.path.exists(dirname):
        return
    try:
        os.mkdir(dirname)
    except BaseException as err:
        print "Error: Can't create directory '"+dirname+"':\n"+str(err)
        sys.exit(2)
    return


def rmdir(dirname):
    if dirname[-1] == os.sep:
        dirname = dirname[:-1]
    if os.path.islink(dirname):
        return # do not clear link - we can get out of dir
    files = os.listdir(dirname)
    for f in files:
        if f == '.' or f == '..':
            continue
        path = dirname + os.sep + f
        if os.path.isdir(path):
            cleardir(path)
        else:
            os.unlink(path)
    os.rmdir(dirname)
    return


def decode_from_hex(text):
    HEXDIGITS = "0123456789abcdefABCDEF"
    only_hex_digits = "".join([c for c in text if c in HEXDIGITS])
    return only_hex_digits.decode("hex")


def parse_char(ch):
    """
    'A' or '\x41' or '41'
    """
    if len(ch) == 1:
        return ord(ch)
    if ch[0:2] == "\\x":
        ch = ch[2:]
    return int(ch, 16)


def dexor(text, key):
    ret = list(text)
    for index, char in enumerate(ret):
        ret[index] = chr(ord(char) ^ ord(key[index % len(key)]))
    return "".join(ret)


def die(exitMessage, exitCode=1):
    print exitMessage
    sys.exit(exitCode)
    return


def is_linux():
    return sys.platform.startswith("linux")


def alphanum(s):
    lst = list(s)
    for index, char in enumerate(lst):
        if char in (string.letters + string.digits):
            continue
        lst[index] = char.encode("hex")
    return "".join(lst)
        
