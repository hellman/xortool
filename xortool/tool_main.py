#!/usr/bin/env python3
from xortool import __version__
__doc__ = f"""
xortool {__version__}
  A tool to do some xor analysis:
  - guess the key length (based on count of equal chars)
  - guess the key (base on knowledge of most frequent char)

Usage:
  xortool [-x] [-m MAX-LEN] [-f] [-t CHARSET] [FILE]
  xortool [-x] [-l LEN] [-c CHAR | -b | -o] [-f] [-t CHARSET] [-p PLAIN] [FILE]
  xortool [-x] [-m MAX-LEN| -l LEN] [-c CHAR | -b | -o] [-f] [-t CHARSET] [-p PLAIN] [FILE]
  xortool [-h | --help]
  xortool --version

Options:
  -x --hex                          input is hex-encoded str
  -l LEN, --key-length=LEN          length of the key
  -m MAX-LEN, --max-keylen=MAX-LEN  maximum key length to probe [default: 65]
  -c CHAR, --char=CHAR              most frequent char (one char or hex code)
  -b --brute-chars                  brute force all possible most frequent chars
  -o --brute-printable              same as -b but will only check printable chars
  -f --filter-output                filter outputs based on the charset
  -t CHARSET --text-charset=CHARSET target text character set [default: printable]
  -p PLAIN --known-plaintext=PLAIN  use known plaintext for decoding
  -h --help                         show this help

Notes:
  Text character set:
    * Pre-defined sets: printable, base32, base64
    * Custom sets:
      - a: lowercase chars
      - A: uppercase chars
      - 1: digits
      - !: special chars
      - *: printable chars

Examples:
  xortool file.bin
  xortool -l 11 -c 20 file.bin
  xortool -x -c ' ' file.hex
  xortool -b -f -l 23 -t base64 message.enc
"""

from operator import itemgetter
import os
import string
import sys

from xortool.args import (
    parse_parameters,
    ArgError,
)
from xortool.charset import CharsetError
from xortool.colors import (
    COLORS,
    C_BEST_KEYLEN,
    C_BEST_PROB,
    C_FATAL,
    C_KEY,
    C_RESET,
    C_WARN,
)
from xortool.routine import (
    decode_from_hex,
    dexor,
    die,
    load_file,
    mkdir,
    rmdir,
    MkdirError,
)


DIRNAME = 'xortool_out'  # here plaintexts will be placed
PARAMETERS = dict()


class AnalysisError(Exception):
    pass


def main():
    try:
        PARAMETERS.update(parse_parameters(__doc__, __version__))
        ciphertext = get_ciphertext()
        if not PARAMETERS["known_key_length"]:
            PARAMETERS["known_key_length"] = guess_key_length(ciphertext)

        if PARAMETERS["brute_chars"]:
            try_chars = range(256)
        elif PARAMETERS["brute_printable"]:
            try_chars = map(ord, string.printable)
        elif PARAMETERS["most_frequent_char"] is not None:
            try_chars = [PARAMETERS["most_frequent_char"]]
        else:
            die(C_WARN +
                "Most possible char is needed to guess the key!" +
                C_RESET)

        (probable_keys,
         key_char_used) = guess_probable_keys_for_chars(ciphertext, try_chars)

        print_keys(probable_keys)
        produce_plaintexts(ciphertext, probable_keys, key_char_used)

    except AnalysisError as err:
        print(C_FATAL + "[ERROR] Analysis error:\n\t", err, C_RESET)
    except ArgError as err:
        print(C_FATAL + "[ERROR] Bad argument:\n\t", err, C_RESET)
    except CharsetError as err:
        print(C_FATAL + "[ERROR] Bad charset:\n\t", err, C_RESET)
    except IOError as err:
        print(C_FATAL + "[ERROR] Can't load file:\n\t", err, C_RESET)
    except MkdirError as err:
        print(C_FATAL + "[ERROR] Can't create directory:\n\t", err, C_RESET)
    except UnicodeDecodeError as err:
        print(C_FATAL + "[ERROR] Input is not hex:\n\t", err, C_RESET)
    else:
        return
    cleanup()
    sys.exit(1)


# -----------------------------------------------------------------------------
# LOADING CIPHERTEXT
# -----------------------------------------------------------------------------

def get_ciphertext():
    """Load ciphertext from a file or stdin and hex-decode if needed"""
    ciphertext = load_file(PARAMETERS["filename"])
    if PARAMETERS["input_is_hex"]:
        ciphertext = decode_from_hex(ciphertext)
    return ciphertext


# -----------------------------------------------------------------------------
# KEYLENGTH GUESSING SECTION
# -----------------------------------------------------------------------------

def guess_key_length(text):
    """
    Try key lengths from 1 to max_key_length and print local maximums

    Set key_length to the most possible if it's not set by user.
    """
    fitnesses = calculate_fitnesses(text)
    if not fitnesses:
        raise AnalysisError("No candidates for key length found! Too small file?")

    print_fitnesses(fitnesses)
    guess_and_print_divisors(fitnesses)
    return get_max_fitnessed_key_length(fitnesses)


def calculate_fitnesses(text):
    """Calculate fitnesses for each keylen"""
    prev = 0
    pprev = 0
    fitnesses = []
    for key_length in range(1, PARAMETERS["max_key_length"] + 1):
        fitness = count_equals(text, key_length)

        # smaller key-length with nearly the same fitness is preferable
        fitness = (float(fitness) /
                   (PARAMETERS["max_key_length"] + key_length ** 1.5))

        if pprev < prev and prev > fitness:  # local maximum
            fitnesses += [(key_length - 1, prev)]

        pprev = prev
        prev = fitness

    if pprev < prev:
        fitnesses += [(key_length - 1, prev)]

    return fitnesses


def print_fitnesses(fitnesses):
    print("The most probable key lengths:")

    # top sorted by fitness, but print sorted by length
    fitnesses.sort(key=itemgetter(1), reverse=True)
    top10 = fitnesses[:10]
    best_fitness = top10[0][1]
    top10.sort(key=itemgetter(0))

    fitness_sum = calculate_fitness_sum(top10)
    fmt = "{C_KEYLEN}{:" + str(len(str(max(i[0] for i in top10)))) + \
            "d}{C_RESET}: {C_PROB}{:5.1f}%{C_RESET}"

    best_colors = COLORS.copy()
    best_colors.update({
        'C_KEYLEN': C_BEST_KEYLEN,
        'C_PROB': C_BEST_PROB,
    })

    for key_length, fitness in top10:
        colors = best_colors if fitness == best_fitness else COLORS
        pct = round(100 * fitness * 1.0 / fitness_sum, 1)
        print(fmt.format(key_length, pct, **colors))


def calculate_fitness_sum(fitnesses):
    return sum([f[1] for f in fitnesses])


def count_equals(text, key_length):
    """Count equal chars count for each offset and sum them"""
    equals_count = 0
    if key_length >= len(text):
        return 0

    for offset in range(key_length):
        chars_count = chars_count_at_offset(text, key_length, offset)
        equals_count += max(chars_count.values()) - 1  # why -1? don't know
    return equals_count


def guess_and_print_divisors(fitnesses):
    """
    Prints common divisors and returns the most common divisor
    """
    divisors_counts = [0] * (PARAMETERS["max_key_length"] + 1)
    for key_length, fitness in fitnesses:
        for number in range(3, key_length + 1):
            if key_length % number == 0:
                divisors_counts[number] += 1
    max_divisors = max(divisors_counts)

    limit = 3
    ret = 2
    fmt = "Key-length can be {C_DIV}{:d}*n{C_RESET}"
    for number, divisors_count in enumerate(divisors_counts):
        if divisors_count == max_divisors:
            print(fmt.format(number, **COLORS))
            ret = number
            limit -= 1
            if limit == 0:
                return ret
    return ret


def get_max_fitnessed_key_length(fitnesses):
    max_fitness = 0
    max_fitnessed_key_length = 0
    for key_length, fitness in fitnesses:
        if fitness > max_fitness:
            max_fitness = fitness
            max_fitnessed_key_length = key_length
    return max_fitnessed_key_length


def chars_count_at_offset(text, key_length, offset):
    chars_count = dict()
    for pos in range(offset, len(text), key_length):
        c = text[pos]
        if c in chars_count:
            chars_count[c] += 1
        else:
            chars_count[c] = 1
    return chars_count


# -----------------------------------------------------------------------------
# KEYS GUESSING SECTION
# -----------------------------------------------------------------------------

def guess_probable_keys_for_chars(text, try_chars):
    """
    Guess keys for list of characters.
    """
    probable_keys = []
    key_char_used = {}

    for c in try_chars:
        keys = guess_keys(text, c)
        for key in keys:
            key_char_used[key] = c
            if key not in probable_keys:
                probable_keys.append(key)

    return probable_keys, key_char_used


def guess_keys(text, most_char):
    """
    Generate all possible keys for key length
    and the most possible char
    """
    key_length = PARAMETERS["known_key_length"]
    key_possible_bytes = [[] for _ in range(key_length)]

    for offset in range(key_length):  # each byte of key<
        chars_count = chars_count_at_offset(text, key_length, offset)
        max_count = max(chars_count.values())
        for char in chars_count:
            if chars_count[char] >= max_count:
                key_possible_bytes[offset].append(char ^ most_char)

    return all_keys(key_possible_bytes)


def all_keys(key_possible_bytes, key_part=(), offset=0):
    """
    Produce all combinations of possible key chars
    """
    keys = []
    if offset >= len(key_possible_bytes):
        return [bytes(key_part)]
    for c in key_possible_bytes[offset]:
        keys += all_keys(key_possible_bytes, key_part + (c,), offset + 1)
    return keys


def print_keys(keys):
    if not keys:
        print("No keys guessed!")
        return

    fmt = "{C_COUNT}{:d}{C_RESET} possible key(s) of length {C_COUNT}{:d}{C_RESET}:"
    print(fmt.format(len(keys), len(keys[0]), **COLORS))
    for key in keys[:5]:
        print(C_KEY + repr(key)[2:-1] + C_RESET)
    if len(keys) > 10:
        print("...")


# -----------------------------------------------------------------------------
# RETURNS PERCENTAGE OF VALID TEXT CHARS
# -----------------------------------------------------------------------------

def percentage_valid(text):
    x = 0.0
    for c in text:
        if c in PARAMETERS["text_charset"]:
            x += 1
    return x / len(text)


# -----------------------------------------------------------------------------
# PRODUCE OUTPUT
# -----------------------------------------------------------------------------

def produce_plaintexts(ciphertext, keys, key_char_used):
    """
    Produce plaintext variant for each possible key,
    creates csv files with keys, percentage of valid
    characters and used most frequent character
    """
    cleanup()
    mkdir(DIRNAME)

    # this is split up in two files since the
    # key can contain all kinds of characters

    fn_key_mapping = "filename-key.csv"
    fn_perc_mapping = "filename-char_used-perc_valid.csv"

    key_mapping = open(os.path.join(DIRNAME,  fn_key_mapping), "w")
    perc_mapping = open(os.path.join(DIRNAME, fn_perc_mapping), "w")

    key_mapping.write("file_name;key_repr\n")
    perc_mapping.write("file_name;char_used;perc_valid\n")

    threshold_valid = 95
    count_valid = 0

    for index, key in enumerate(keys):
        key_index = str(index).rjust(len(str(len(keys) - 1)), "0")
        key_repr = repr(key)
        file_name = os.path.join(DIRNAME, key_index + ".out")

        dexored = dexor(ciphertext, key)
        # ignore saving file when known plain is provided and output doesn't contain it
        if PARAMETERS["known_plain"] and PARAMETERS["known_plain"] not in dexored:
            continue
        perc = round(100 * percentage_valid(dexored))
        if perc > threshold_valid:
            count_valid += 1
        key_mapping.write("{};{}\n".format(file_name, key_repr))
        perc_mapping.write("{};{};{}\n".format(file_name,
                                               repr(key_char_used[key]),
                                               perc))
        if not PARAMETERS["filter_output"] or \
            (PARAMETERS["filter_output"] and perc > threshold_valid):
            f = open(file_name, "wb")
            f.write(dexored)
            f.close()
    key_mapping.close()
    perc_mapping.close()

    fmt = "Found {C_COUNT}{:d}{C_RESET} plaintexts with {C_COUNT}{:d}{C_RESET}%+ valid characters"
    if PARAMETERS["known_plain"]:
        escaped_plain = PARAMETERS["known_plain"].decode('ascii')
        escaped_plain = escaped_plain.replace("{", "{{").replace("}", "}}")

        fmt += " which contained '{}'".format(escaped_plain)
    print(fmt.format(count_valid, round(threshold_valid), **COLORS))
    print("See files {}, {}".format(fn_key_mapping, fn_perc_mapping))


def cleanup():
    if os.path.exists(DIRNAME):
        rmdir(DIRNAME)


if __name__ == "__main__":
    main()
