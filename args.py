#!/usr/bin/env python
#-*- coding:utf-8 -*-

import getopt

from routine import *

def parse_arguments(arguments_list, PARAMETERS):
    """
    Parse arguments and update PARAMETERS if needed
    """
    options, real_arguments = get_options_and_arguments(arguments_list)
    return update_parameters(PARAMETERS, options, real_arguments)


def get_options_and_arguments(program_arguments):
    options, arguments = [], []
    try:
        options, arguments = getopt.getopt(program_arguments, "l:c:s:m:x",
                ["key-length=", "char=", "spread=", "max-keylen=",
                                          "hex", "help", "usage"])
        if len(arguments) > 1:  # trick to parse options after filename
            options += get_options_and_arguments(program_arguments[1:])[0]
            arguments = arguments[:1]
        #TODO: add param "brute all possible freq. chars"
        
    except getopt.GetoptError:
        show_usage_and_exit()
    return options, arguments


def update_parameters(PARAMETERS, options, arguments):
    #print "OPTS", options
    #print "ARGS", arguments
    for option, value in options:
        if option in ("-x", "--hex"):
            PARAMETERS["input_is_hex"] = 1
        elif option in ("-c", "--char"):
            PARAMETERS["most_frequent_char"] = parse_char(value)
        elif option in ("-l", "--key-length"):
            PARAMETERS["known_key_length"] = int(value)
        elif option in ("-s", "--spread"):
            PARAMETERS["frequency_spread"] = int(value)
        elif option in ("-m", "--max-keylen"):
            PARAMETERS["max_key_length"] = int(value)
        elif option in ("-h", "--help", "--usage"):
            show_usage_and_exit()
            
    if len(arguments) == 1:
        PARAMETERS["filename"] = arguments[0]

    return PARAMETERS


def show_usage_and_exit():
    print "xortool.py"
    print "  A tool to do some xor analysis:"
    print "  - guess the key length (based on count of equal chars)"
    print "  - guess the key (base on knowledge of most probable char)"
    print "Usage:"
    print " ", os.path.basename(sys.argv[0]),"[-h|--help] [OPTIONS] [<filename>]"
    print "Options:"
    print " ", "-l,--key-length     length of the key"
    print " ", "-c,--char           most possible char"
    print " ", "-x,--hex            input is hex-encoded str"
    print " ", "-s,--spread         spread of possible key bytes"
    print " ", "-m,--max-keylen     maximum key length to probe"
    sys.exit(1)
    return
