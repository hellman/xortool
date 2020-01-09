import os
import sys
import string


class MkdirError(Exception):
    pass


def load_file(filename):
    if filename == "-":
        filename = sys.stdin.fileno()
    with open(filename, "rb") as fd:
        return fd.read()


def save_file(filename, data):
    with open(filename, "wb") as fd:
        fd.write(data)


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

def decode_from_hex(text):
    text = text.decode(encoding='ascii', errors='ignore')
    only_hex_digits = "".join(c for c in text if c in string.hexdigits)
    return bytes.fromhex(only_hex_digits)


def dexor(text, key):
    mod = len(key)
    return bytes(key[index % mod] ^ char for index, char in enumerate(text))


def die(exitMessage, exitCode=1):
    print(exitMessage)
    sys.exit(exitCode)


def is_linux():
    return sys.platform.startswith("linux")


def alphanum(s):
    lst = list(s)
    for index, char in enumerate(lst):
        if char in string.ascii_letters + string.digits:
            continue
        lst[index] = char.hex()
    return "".join(lst)
