#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import string


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


def get_charset(charset):
    charset = charset or "printable"
    if charset in PREDEFINED_CHARSETS.keys():
        return PREDEFINED_CHARSETS[charset]
    try:
        _ = ""
        for c in set(charset):
            _ += CHARSETS[c]
        return _
    except KeyError as err:
        raise CharsetError("Bad character set")
