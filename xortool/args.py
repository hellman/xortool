from __future__ import annotations

from typing import Any, Literal, cast, overload, TypedDict
from docopt import docopt

from xortool.charset import get_charset

class ParameterDict(TypedDict):

    brute_chars: bool
    brute_printable: bool
    filename: str
    filter_output: bool
    frequency_spread: int
    input_is_hex: bool
    known_key_length: int | None
    max_key_length: int | None
    most_frequent_char: int | None
    text_charset: str | bytes
    known_plain: bytes | Literal[False]
    threshold: int | None



class ArgError(Exception):
    pass

@overload
def parse_char(ch: None) -> None: ...

@overload
def parse_char(ch: str) -> int: ...

def parse_char(ch: str | None) -> int | None:
    """
    'A' or '\x41' or '0x41' or '41'
    '\x00' or '0x00' or '00'
    """
    if ch is None:
        return None
    if len(ch) == 1:
        return ord(ch)
    if ch[0:2] in ("0x", "\\x"):
        ch = ch[2:]
    if not ch:
        raise ValueError("Empty char")
    if len(ch) > 2:
        raise ValueError("Char can be only a char letter or hex")
    return int(ch, 16)

@overload
def parse_int(i: None) -> None: ...

@overload
def parse_int(i: str) -> int: ...

def parse_int(i: str | None) -> int | None:
    if i is None:
        return None
    return int(i)


def parse_parameters(doc: str, version: str) -> ParameterDict:
    p = docopt(doc, version=version)
    p = {k.lstrip("-"): v for k, v in p.items()}
    try:
        return {
            "brute_chars": bool(p["brute-chars"]),
            "brute_printable": bool(p["brute-printable"]),
            "filename": p["FILE"] if p["FILE"] else "-",  # stdin by default
            "filter_output": bool(p["filter-output"]),
            "frequency_spread": 0,  # to be removed
            "input_is_hex": bool(p["hex"]),
            "known_key_length": parse_int(p["key-length"]),
            "max_key_length": parse_int(p["max-keylen"]),
            "most_frequent_char": parse_char(p["char"]),
            "text_charset": get_charset(p["text-charset"]),
            "known_plain": p["known-plaintext"].encode() if p["known-plaintext"] else False,
            "threshold": parse_int(p["threshold"]),
        }
    except ValueError as err:
        raise ArgError(str(err))
