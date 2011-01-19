#!/usr/bin/env python
#-*- coding:utf-8 -*-
# ---------------------------------------------------------------
# xortool.py
#   tool to do some xor analysis
# Usage:
#   xortool [-h|--help] [OPTIONS] [<filename>]
# Options:
#   -l,--key-length     length of the key
#   -c,--char           most possible char
#   -x,--hex            input is hex-encoded str
#   -s,--spread         spread of possible key bytes
#   -m,--max-keylen     maximum key length to probe
# Examples:
#   xortool file.bin
#   xortool -x -l 4 -c ' ' file.hex
# ---------------------------------------------------------------
# Author: hellman ( hellman1908@gmail.com )
# ---------------------------------------------------------------

import os, sys
import getopt
import string

DEBUG = 0
DIRNAME = 'xortool'

def usage():
    print "xortool.py"
    print "  A tool to do some xor analysis:"
    print "  - guess the key length (based on count of equal chars)"
    print "  - guess the key (base on knowlede of most probable char)"
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


def mkdir(dirname):
    if os.path.exists(dirname):
        return
    try:
        os.mkdir(dirname)
    except BaseException as err:
        print "ERror: Can't create directory '"+dirname+"':\n"+str(err)
        sys.exit(2)
    return


def cleardir(dirname):
    if dirname[-1] == os.sep:
        dirname = dirname[:-1]
    files = os.listdir(dirname)
    for f in files:
        if f == '.' or f == '..':
            continue
        path = dirname + os.sep + f
        if os.path.isdir(path):
            cleardir(path)
        else:
            os.unlink(path)
    os.rmdir(dirname)
    return


def parse_char(ch):
    if len(ch) == 1:
        return ord(ch)
    if ch[0:2] == "\\x":
        ch = ch[2:]
    return int(ch, 16)


def file_contents(filename):
    text = ''
    try:
        if filename == "-":
            text = sys.stdin.read()
        else:
            fd = open(filename, "r")
            text = fd.read()
            fd.close()
    except BaseException as err:
        print "ERror: Can't open '"+filename+"':\n"+str(err)
        sys.exit(2)
    return text


#--------------------------------------------------
# Try key lengths from 1 to max_keylen
# and print local maximums
#--------------------------------------------------
def try_lengths(text, max_keylen):

    # initial states
    pprev = 0
    prev = 0
    fitnesses = []
    fitness_sum = 0

    # for each key length
    for keylen in range(1, max_keylen+1):
        if keylen == len(text):
            break
        equals_count = 0
        
        # COUNT EQUAL CHARS COUNT FOR EACH OFFSET AND SUM THEM
        for offset in range(keylen):
            chars_count = dict()
            pos = offset
            while pos < len(text):
                c = text[pos]
                if c in chars_count:
                    chars_count[c] += 1
                else:
                    chars_count[c] = 1
                pos += keylen
            equals_count += max(chars_count.values())-1
            #print '    appended',max(chars_count.values())
        
        # CALCULATE PROBABILITY OF KEYLEN
        fitness = equals_count
        
        # PRINT ALL KEYS' LENGTHS AND FITNESSES
        if 0 or DEBUG:
            print "length",keylen,":",fitness
        
        # PRINT LOCAL FITNESSES' MAXIMUMS
        if pprev < prev and prev > fitness:
            fitness_sum += prev
            fitnesses += [(keylen-1, prev)]
            #print 'added',prev,'=',fitness_sum,'(keylen =', keylen-1, ')'
        pprev = prev
        prev = fitness
    print fitnesses
    print fitness_sum
    # PRINT PROBABILITY AND GUESS divizor FORM OF KEY
    print "Probable key lengths:"
    max_divizors = 0
    #main_number = -1
    divizors_counts = [ 0 for i in range(keylen+1) ]
    ret = 2
    ret_fit = 0
    for keylen, fitness in fitnesses:
        print str(keylen).rjust(4," ")+":  ", round(100*fitness*1.0/fitness_sum, 1,), "%"
        if fitness > ret_fit:
            ret = keylen
            ret_fit = fitness
        for number in range(3, keylen+1):
            if keylen % number == 0:
                divizors_counts[number] += 1
    max_divizors = max(divizors_counts)
    for number in range(len(divizors_counts)):
        if divizors_counts[number] == max_divizors:
            print "Key-length should be "+str(number)+"*n"
            #ret = number
    return ret


#--------------------------------------------------
# just xor text with the key
#--------------------------------------------------
def dexor(s, key):
    ret = list(s)
    for i in range(len(ret)):
        ret[i] = chr(ord(ret[i]) ^ ord(key[i % len(key)]))
    return "".join(ret)


#--------------------------------------------------
# Generate all possible keys for key length 
# and the most possible char 
#--------------------------------------------------
def gen_key(text, key_length, most_char, spread):

    # FIND OUT THE MOST POSSIBLE BYTES OF THE KEY
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
            if maxcount > char_count[c]+spread:
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
    for i in range(len(keys)):
        key = keys[i]
        fname = []
        for c in key:
            if c in string.letters or c in string.digits:
                fname.append(c)
            else:
                fname.append(c.encode("hex"))
        f = open(os.path.join(DIRNAME, str(i).rjust(3 if len(keys) >= 100 else 2,"0")+"_"+"".join(fname)), "w")
        f.write(dexor(text, key))
        f.close()
         
    return


#--------------------------------------------------
# Produce all combinations of possible key chars
#--------------------------------------------------
def all_keys(key_possible_bytes, key_part, offset):
    ret = []
    if offset >= len(key_possible_bytes):
        return [key_part];
    for c in key_possible_bytes[offset]:
        ret += all_keys(key_possible_bytes, key_part + chr(c), offset+1) # hate recursion >_<
    return ret




#--------------------------------------------------
# Parse arguments and do the work
#--------------------------------------------------
def main():
    
    # default parameters
    fromhex = 0
    spread = 0
    most_char = None
    keylen = None
    max_keylen = 32
    
    # PARSING ARGUMENTS
    try:
        opts, args = getopt.getopt(sys.argv[1:], "l:c:s:m:x", ["key-length", "char", "spread", "max-keylen", "hex", "help", "usage"])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in ("-x", "--hex"):
            fromhex = 1
        if opt in ("-c", "--char"):
            most_char = parse_char(arg)
        if opt in ("-l", "--key-length"):
            keylen = int(arg)
        if opt in ("-s", "--spread"):
            spread = int(arg)
        if opt in ("-m", "--max-keylen"):
            max_keylen = int(arg)
        if opt in ("-h", "--help", "--usage"):
            usage()
    
    # LOADING FILE
    fname = ''
    if len(args) > 1:
        print "OPTIONS should precede <filename\n"
        sys.exit(1)
    if len(args) < 1:
        fname = "-"
    else:
        fname = args[0]
    text = file_contents(fname)
    if not text:
        print "No input! (Maybe file is empty)"
        sys.exit(1)
    if fromhex:
        text = "".join([c for c in text if c in "0123456789abcdefABCDEF"]).decode("hex")
    
    # PROBING KEYLENs
    if keylen == None:
        keylen = try_lengths(text, max_keylen)
    
    # PROBING KEY
    if most_char != None:
        gen_key(text, keylen, most_char, spread)
    else:
        if keylen != None:
            print "Most possible char is needed to guess the key!"
    
    return


if __name__ == "__main__":
    main()
