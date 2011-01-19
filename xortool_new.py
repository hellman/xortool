#!/usr/bin/env python
#-*- coding:utf-8 -*-
# ---------------------------------------------------------------
# xortool.py
#   A tool to do some xor analysis:"
#   - guess the key length (based on count of equal chars)"
#   - guess the key (base on knowledge of most frequent char)"
# Usage:
#   xortool [-h|--help] [OPTIONS] [<filename>]
# Options:
#   -l,--key-length     length of the key
#   -c,--char           most frequent char
#   -x,--hex            input is hex-encoded str
#   -s,--spread         spread of possible key bytes
#   -m,--max-keylen     maximum key length to probe
# Examples:
#   xortool file.bin
#   xortool -x -l 4 -c ' ' file.hex
# ---------------------------------------------------------------
# Author: hellman ( hellman1908@gmail.com )
# ---------------------------------------------------------------

import os
import sys
import getopt

from routine import *
from args import parse_arguments

DEBUG = 0
DIRNAME = 'xortool'

PARAMETERS = {
    "input_is_hex": 0,
    "max_key_length": 32,
    "known_key_length": None,
    "most_frequent_char": None,
    "frequency_spread": 0,
    "filename": "-", # stdin by default
}

def main():
    global PARAMETERS
    PARAMETERS = parse_arguments(sys.argv[1:], PARAMETERS)
    
    ciphertext = get_ciphertext()
    update_key_length(ciphertext)
    probable_keys = guess_probable_keys(ciphertext)
    
    #produce_plaintexts(ciphertext, probable_keys)
    return

# ----------------------------------------------------------------------------

def get_ciphertext():
    """
    Load ciphertext from a file or stdin and hex-decode if needed
    """
    ciphertext = load_file(PARAMETERS["filename"])
    if PARAMETERS["input_is_hex"]:
        ciphertext = decode_from_hex(ciphertext)
    return ciphertext


def update_key_length(text):
    """
    Guess length of the key if it's not set. (Updates PARAMETERS)
    """
    global PARAMETERS
    if PARAMETERS["known_key_length"]:
        return
    PARAMETERS["known_key_length"] = guess_key_length(text)
    return


def guess_probable_keys(text):
    """
    Guess key if the most frequent char is known.
    """
    probable_keys = []
    if PARAMETERS["most_frequent_char"] is None:
        die("Most possible char is needed to guess the key!")
    else:
        probable_keys = guess_keys(text)
    return probable_keys

#--------------------------------------------------

def guess_key_length(text):
    """
    Try key lengths from 1 to max_key_length and print local maximums.
    Set key_length to the most possible if it's not set by user.
    """
    fitnesses = calculate_fitnesses(text)
    print_fitnesses(fitnesses)
    return guess_and_print_divizors(fitnesses)


def calculate_fitnesses(text):
    """
    Calc. fitnesses for each keylen
    """
    prev = 0
    pprev = 0
    fitnesses = []
    for keylen in range(1, PARAMETERS["max_key_length"]+1):
        fitness = count_equals(keylen, text)
        
        if pprev < prev and prev > fitness:  # local maximum
            fitnesses += [(keylen-1, prev)]

        pprev = prev
        prev = fitness
        
    return fitnesses


def print_fitnesses(fitnesses):
    print "Probable key lengths:"
    fitness_sum = calculate_fitness_sum(fitnesses)
    for keylen, fitness in fitnesses:
        print str(keylen).rjust(4," ")+":  ",
        print round(100*fitness/fitness_sum, 1,), "%"
    return
    

def calculate_fitness_sum(fitnesses):
    return sum([f for (keylen, f) in fitnesses])


def count_equals(keylen, text):
    """
    count equal chars count for each offset and sum them
    """
    equals_count = 0
    if keylen >= len(text):
        return 0

    for offset in range(keylen):
        chars_count = dict()
        for pos in range(offset, len(text), keylen):
            c = text[pos]
            if c in chars_count:
                chars_count[c] += 1
            else:
                chars_count[c] = 1
        equals_count += max(chars_count.values()) #-1?

    return equals_count


def guess_and_print_divizors(fitnesses):
    """
    Prints common divizors and returns the most common divizor
    """
    divizors_counts = [ 0 for i in range(PARAMETERS["max_key_length"]+1) ]
    for keylen, fitness in fitnesses:
        for number in range(3, keylen+1):
            if keylen % number == 0:
                divizors_counts[number] += 1
    max_divizors = max(divizors_counts)
    
    ret = 2
    for number in range(len(divizors_counts)):
        if divizors_counts[number] == max_divizors:
            print "Key-length can be "+str(number)+"*n"
            ret = number
    return ret


def guess_keys(text):
    """
    Generate all possible keys for key length 
    and the most possible char     
    """
    key_length = PARAMETERS["known_key_length"]
    most_char = PARAMETERS["most_frequent_char"]
    key_possible_bytes = [[] for i in range(key_length)]
    for i in range(key_length): #each byte of key
        maxcount = 0
        pos = i
        char_count = dict()
        while pos < len(text):
            c = text[pos]
            if c in char_count:
                char_count[c] += 1
                if char_count[c] >= maxcount:
                    maxcount = char_count[c]
            else:
                char_count[c] = 1
            pos += key_length
            
        for c in char_count:
            if maxcount > char_count[c]:
                continue
            key_possible_bytes[i] += [ord(c) ^ most_char]

    # PRINT ALL PROBABLE KEYS
    print "Probable keys: "
    keys = all_keys(key_possible_bytes, "", 0)
    print keys
    
    # MKDIR FOR OUTPUT
    if os.path.exists(DIRNAME):
        cleardir(DIRNAME)
    mkdir(DIRNAME)
    
    # MAKE dexor'd OUTPUT FOR EACH KEY
    for key in keys:
         f = open(os.path.join("xortool", key.encode("hex")), "w")
         f.write(dexor(text, key))
         f.close()
         
    return


def all_keys(key_possible_bytes, key_part, offset):
    """
    Produce all combinations of possible key chars
    """
    ret = []
    if offset >= len(key_possible_bytes):
        return [key_part];
    for c in key_possible_bytes[offset]:
        ret += all_keys(key_possible_bytes, key_part + chr(c), offset+1) # hate recursion >_<
    return ret


def dexor(s, key):
    ret = list(s)
    for i in range(len(ret)):
        ret[i] = chr(ord(ret[i]) ^ ord(key[i % len(key)]))
    return "".join(ret)


def die(exitMessage, exitCode=1):
    print exitMessage
    sys.exit(exitCode)
    return


if __name__ == "__main__":
    main()
