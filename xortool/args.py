#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from docopt import docopt

from xortool.routine import parse_char
from xortool.charset import get_charset


class ArgError(Exception):
    pass


def parse_parameters(doc, version):
    p = docopt(doc, version=version)
    p = {k.lstrip("-"): v for k, v in p.items()}
    try:
        return {
            "input_is_hex": bool(p["hex"]),
            "max_key_length": int(p["max-keylen"]),
            "known_key_length": int(p["key-length"]) if p["key-length"] else None,
            "most_frequent_char": parse_char(p["char"]) if p["char"] else None,
            "brute_chars": bool(p["brute-chars"]),
            "brute_printable": bool(p["brute-printable"]),
            "text_charset": get_charset(p["text-charset"]),
            "frequency_spread": 0,  # to be removed
            "filename": p["FILE"] if p["FILE"] else "-",  # stdin by default
            "filter_output": bool(p["filter-output"]),
        }
    except ValueError as err:
        raise ArgError(str(err))
