from __future__ import annotations

import os
import sys
import string


class MkdirError(Exception):
    pass


def load_file(filename: str | int) -> bytes:
    if filename == "-":
        filename = sys.stdin.fileno()
    with open(filename, "rb") as fd:
        return fd.read()


def save_file(filename: str, data: bytes) -> None:
    with open(filename, "wb") as fd:
        fd.write(data)


def mkdir(dirname: str) -> None:
    if os.path.exists(dirname):
        return
    try:
        os.mkdir(dirname)
    except BaseException as err:
        raise MkdirError(str(err))


def rmdir(dirname: str) -> None:
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

def decode_from_hex(text: bytes) -> bytes:
    text_bytes = text.decode(encoding='ascii', errors='ignore')
    only_hex_digits = "".join(c for c in text_bytes if c in string.hexdigits)
    return bytes.fromhex(only_hex_digits)


def dexor(text: bytes, key: bytes) -> bytes:
    mod = len(key)
    return bytes(key[index % mod] ^ char for index, char in enumerate(text))


def die(exitMessage: str, exitCode: int = 1) -> None:
    print(exitMessage)
    sys.exit(exitCode)


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def alphanum(s: str) -> str:
    lst = list(s)
    for index, char in enumerate(lst):
        if char in string.ascii_letters + string.digits:
            continue
        lst[index] = char.encode("ascii").hex()
    return "".join(lst)
