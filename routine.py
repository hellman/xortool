#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys

def load_file(filename):
    if filename == "-":
        return sys.stdin.read()
    fd = open(filename, "r")
    contents = fd.read()
    fd.close()
    return contents


def save_file(filename, data):
    fd = open(filename, "w")
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


def cleardir(dirname):
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
