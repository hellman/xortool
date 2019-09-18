from docopt import docopt

from xortool.charset import get_charset


class ArgError(Exception):
    pass


def parse_char(ch):
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


def parse_int(i):
    if i is None:
        return None
    return int(i)


def parse_parameters(doc, version):
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
        }
    except ValueError as err:
        raise ArgError(str(err))
