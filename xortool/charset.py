#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import string

import numpy as np


class CharsetError(Exception):
    pass


CHARSETS = {
    "a": string.ascii_lowercase,
    "A": string.ascii_uppercase,
    "1": string.digits,
    "!": string.punctuation,
    "*": string.printable,
}

PREDEFINED_CHARSETS = {
    "base32":    CHARSETS["A"] + "234567=",
    "base64":    CHARSETS["a"] + CHARSETS["A"] + CHARSETS["1"] + "/+=",
    "printable": CHARSETS["*"],
}


def _get_charset_string(charset):
    charset = charset or "printable"
    if charset in PREDEFINED_CHARSETS.keys():
        return PREDEFINED_CHARSETS[charset]
    try:
        _ = ""
        for c in set(charset):
            _ += CHARSETS[c]
        return _
    except KeyError:
        raise CharsetError("Bad character set: ", charset)


def get_charset(charset):
    charset_string = _get_charset_string(charset)
    return np.array(list(bytes(charset_string, 'utf8')), dtype=np.uint8)
