#!/usr/bin/env python
#-*- coding:utf-8 -*-

import getopt

from routine import *


class ArgError(Exception):
    pass


PARAMETERS = {
    "input_is_hex": 0,
    "max_key_length": 65,
    "known_key_length": None,
    "most_frequent_char": None,
    "brute_chars": None,
    "brute_printable": None,
    "frequency_spread": 0,
    "filename": "-",  # stdin by default
}


def show_usage_and_exit():
    print """xortool.py
A tool to do some xor analysis:
  - guess the key length (based on count of equal chars)
  - guess the key (base on knowledge of most probable char)
Usage:
  {} [-h|--help] [OPTIONS] [<filename>]
Options:
  -l,--key-length       length of the key (integer)
  -c,--char             most possible char (one char or hex code)
  -m,--max-keylen=32    maximum key length to probe (integer)
  -x,--hex              input is hex-encoded str
  -b,--brute-chars      brute force all possible characters
  -o,--brute-printable  same as -b but will only use printable
                        characters for keys
                        """.format(os.path.basename(sys.argv[0]))
    sys.exit(1)


def parse_parameters():
    """
    Parse arguments and update PARAMETERS if needed
    """
    options, arguments = get_options_and_arguments(sys.argv[1:])
    update_parameters(options, arguments)
    return PARAMETERS


def get_options_and_arguments(program_arguments):
    options, arguments = [], []
    try:
        options, arguments = getopt.gnu_getopt(program_arguments,
                                               "l:c:s:m:xbo",
                                               ["key-length=",
                                                "char=",
                                                "spread=",
                                                "max-keylen=",
                                                "hex",
                                                "help",
                                                "usage",
                                                "brute-chars",
                                                "brute-printable"])

    except getopt.GetoptError:
        show_usage_and_exit()
    return options, arguments


def update_parameters(options, arguments):
    global PARAMETERS
    try:
        for option, value in options:
            if option in ("-x", "--hex"):
                PARAMETERS["input_is_hex"] = 1
            elif option in ("-c", "--char"):
                PARAMETERS["most_frequent_char"] = parse_char(value)
            elif option in ("-l", "--key-length"):
                PARAMETERS["known_key_length"] = int(value)
            elif option in ("-b", "--brute-chars"):
                PARAMETERS["brute_chars"] = True
            elif option in ("-o", "--brute-printable"):
                PARAMETERS["brute_printable"] = True
            elif option in ("-s", "--spread"):
                PARAMETERS["frequency_spread"] = int(value)
            elif option in ("-m", "--max-keylen"):
                PARAMETERS["max_key_length"] = int(value)
            elif option in ("-h", "--help", "--usage"):
                show_usage_and_exit()
            else:
                raise ArgError("Unknown argument: {0}".format(option))
    except ValueError as err:
        raise ArgError(str(err))

    if ((PARAMETERS["most_frequent_char"] and PARAMETERS["brute_printable"]
         or
         PARAMETERS["most_frequent_char"] and PARAMETERS["brute_chars"]
         or
         PARAMETERS["brute_printable"] and PARAMETERS["brute_chars"])):
        raise ArgError("Only one out of -c, -b or -o should be used")

    if len(arguments) == 1:
        PARAMETERS["filename"] = arguments[0]

    return
