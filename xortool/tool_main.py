#!/usr/bin/env python3
import os
import string
import sys
from operator import itemgetter
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.style import Style

from xortool import __version__
from xortool.args import ArgError
from xortool.charset import CharsetError, get_charset
from xortool.routine import (
    MkdirError,
    decode_from_hex,
    dexor,
    die,
    load_file,
    mkdir,
    rmdir,
)

app = typer.Typer(add_completion=False)
DIRNAME = "xortool_out"
PARAMETERS = dict()

console = Console()
STYLE_BEST_KEYLEN = Style(color="cyan", bold=True)
STYLE_BEST_PROB = Style(color="magenta", bold=True)
STYLE_FATAL = Style(color="red", bold=True)
STYLE_KEY = Style(color="yellow", bold=True)
STYLE_WARN = Style(color="yellow")
STYLE_COUNT = Style(color="green", bold=True)
STYLE_KEYLEN = Style(color="blue", bold=True)
STYLE_PROB = Style(color="magenta")
STYLE_RESET = Style()  # default


class AnalysisError(Exception):
    pass


def cleanup():
    if os.path.exists(DIRNAME):
        rmdir(DIRNAME)


def get_ciphertext():
    ciphertext = load_file(PARAMETERS["filename"])
    if PARAMETERS["input_is_hex"]:
        ciphertext = decode_from_hex(ciphertext)
    return ciphertext


def calculate_fitnesses(text):
    prev = 0
    pprev = 0
    fitnesses = []
    key_length = 1  # Initialize key_length
    for key_length in range(1, PARAMETERS["max_key_length"] + 1):
        fitness = count_equals(text, key_length)

        fitness = float(fitness) / (PARAMETERS["max_key_length"] + key_length**1.5)

        if pprev < prev and prev > fitness:
            fitnesses += [(key_length - 1, prev)]

        pprev = prev
        prev = fitness

    if pprev < prev:
        fitnesses += [(key_length - 1, prev)]

    return fitnesses


def count_equals(text, key_length):
    equals_count = 0
    if key_length >= len(text):
        return 0

    for offset in range(key_length):
        chars_count = chars_count_at_offset(text, key_length, offset)
        equals_count += max(chars_count.values()) - 1
    return equals_count


def guess_and_print_divisors(fitnesses):
    divisors_counts = [0] * (PARAMETERS["max_key_length"] + 1)
    for key_length, fitness in fitnesses:
        for number in range(3, key_length + 1):
            if key_length % number == 0:
                divisors_counts[number] += 1
    max_divisors = max(divisors_counts)

    limit = 3
    ret = 2
    for number, divisors_count in enumerate(divisors_counts):
        if divisors_count == max_divisors:
            console.print(
                f"Key-length can be [bold blue]{number}[/]", style=STYLE_KEYLEN
            )
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


def guess_probable_keys_for_chars(text, try_chars):
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
    key_length = PARAMETERS["known_key_length"]
    key_possible_bytes = [[] for _ in range(key_length)]

    for offset in range(key_length):
        chars_count = chars_count_at_offset(text, key_length, offset)
        max_count = max(chars_count.values())
        for char in chars_count:
            if chars_count[char] >= max_count:
                key_possible_bytes[offset].append(char ^ most_char)

    return all_keys(key_possible_bytes)


def all_keys(key_possible_bytes, key_part=(), offset=0):
    keys = []
    if offset >= len(key_possible_bytes):
        return [bytes(key_part)]
    for c in key_possible_bytes[offset]:
        keys += all_keys(key_possible_bytes, key_part + (c,), offset + 1)
    return keys


def print_keys(keys):
    if not keys:
        console.print("No keys guessed!", style=STYLE_WARN)
        return

    fmt = "[green]{:d}[/] possible key(s) of length [green]{:d}[/]:"
    console.print(fmt.format(len(keys), len(keys[0])), style=STYLE_COUNT)
    for key in keys[:5]:
        console.print(repr(key)[2:-1], style=STYLE_KEY)
    if len(keys) > 10:
        console.print("...")


def percentage_valid(text: bytes):
    x = 0.0
    for c in text:
        if c in PARAMETERS["text_charset"]:
            x += 1
    return x / len(text)


def produce_plaintexts(ciphertext, keys, key_char_used):
    cleanup()
    mkdir(DIRNAME)

    fn_key_mapping = "filename-key.csv"
    fn_perc_mapping = "filename-char_used-perc_valid.csv"

    key_mapping = open(os.path.join(DIRNAME, fn_key_mapping), "w")
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
        if PARAMETERS["known_plain"] and PARAMETERS["known_plain"] not in dexored:
            continue
        perc = round(100 * percentage_valid(dexored))
        if perc > threshold_valid:
            count_valid += 1
        key_mapping.write("{};{}\n".format(file_name, key_repr))
        perc_mapping.write(
            "{};{};{}\n".format(file_name, repr(key_char_used[key]), perc)
        )
        if not PARAMETERS["filter_output"] or (
            PARAMETERS["filter_output"] and perc > threshold_valid
        ):
            f = open(file_name, "wb")
            f.write(dexored)
            f.close()
    key_mapping.close()
    perc_mapping.close()

    msg = f"Found [green]{count_valid}[/] plaintexts with [green]{round(threshold_valid)}[/]%+ valid characters"
    if PARAMETERS["known_plain"]:
        msg += f" which contained '{PARAMETERS['known_plain'].decode('ascii')}'"
    console.print(msg)
    console.print(f"See files {fn_key_mapping}, {fn_perc_mapping}")


def cli_main(
    filename: Annotated[
        Optional[str],
        typer.Argument(help="Input file (or stdin if omitted)", show_default=False),
    ] = None,
    hex: Annotated[
        bool, typer.Option("--hex", "-x", help="Input is hex-encoded str")
    ] = False,
    key_length: Annotated[
        Optional[int], typer.Option("--key-length", "-l", help="Length of the key")
    ] = None,
    max_keylen: Annotated[
        int, typer.Option("--max-keylen", "-m", help="Maximum key length to probe")
    ] = 65,
    char: Annotated[
        Optional[str],
        typer.Option("--char", "-c", help="Most frequent char (one char or hex code)"),
    ] = None,
    brute_chars: Annotated[
        bool,
        typer.Option(
            "--brute-chars", "-b", help="Brute force all possible most frequent chars"
        ),
    ] = False,
    brute_printable: Annotated[
        bool,
        typer.Option(
            "--brute-printable",
            "-o",
            help="Same as -b but will only check printable chars",
        ),
    ] = False,
    filter_output: Annotated[
        bool,
        typer.Option(
            "--filter-output", "-f", help="Filter outputs based on the charset"
        ),
    ] = False,
    text_charset: Annotated[
        Optional[str],
        typer.Option(
            "--text-charset",
            "-t",
            help="""Target text character set

- Custom sets:

  - a: lowercase chars

  - A: uppercase chars

  - 1: digits

  - !: special chars

  - *: printable chars""",
        ),
    ] = None,
    known_plain: Annotated[
        Optional[str],
        typer.Option(
            "--known-plaintext", "-p", help="Use known plaintext for decoding"
        ),
    ] = None,
    version: Annotated[
        bool, typer.Option("--version", help="Show version and exit")
    ] = False,
):
    """
    A tool to do some xor analysis:

    - guess the key length (based on count of equal chars)

    - guess the key (base on knowledge of most frequent char)
    """
    if version:
        typer.echo(__version__)
        raise typer.Exit()

    PARAMETERS.clear()
    PARAMETERS["filename"] = filename
    PARAMETERS["input_is_hex"] = hex
    PARAMETERS["known_key_length"] = key_length
    PARAMETERS["max_key_length"] = max_keylen
    PARAMETERS["most_frequent_char"] = (
        ord(char) if char and len(char) == 1 else (int(char, 16) if char else None)
    )
    PARAMETERS["brute_chars"] = brute_chars
    PARAMETERS["brute_printable"] = brute_printable
    PARAMETERS["filter_output"] = filter_output
    PARAMETERS["text_charset"] = get_charset(text_charset)
    PARAMETERS["known_plain"] = known_plain.encode() if known_plain else None

    try:
        ciphertext = get_ciphertext()
        if not PARAMETERS["known_key_length"]:
            PARAMETERS["known_key_length"] = guess_key_length(ciphertext)
            try_chars = [PARAMETERS["most_frequent_char"]]
        if PARAMETERS["brute_chars"]:
            try_chars = range(256)
        elif PARAMETERS["brute_printable"]:
            try_chars = map(ord, string.printable)
        elif PARAMETERS["most_frequent_char"] is not None:
            try_chars = [PARAMETERS["most_frequent_char"]]
        else:
            console.print(
                "Most possible char is needed to guess the key!", style=STYLE_WARN
            )
            die("Most possible char is needed to guess the key!")
            try_chars = [PARAMETERS["most_frequent_char"]]

        (probable_keys, key_char_used) = guess_probable_keys_for_chars(
            ciphertext, try_chars
        )

        print_keys(probable_keys)
        produce_plaintexts(ciphertext, probable_keys, key_char_used)
    # [TODO]
    except AnalysisError as err:
        console.print(f"[ERROR] Analysis error:\n\t{err}", style=STYLE_FATAL)
    except ArgError as err:
        console.print(f"[ERROR] Bad argument:\n\t{err}", style=STYLE_FATAL)
    except CharsetError as err:
        console.print(f"[ERROR] Bad charset:\n\t{err}", style=STYLE_FATAL)
    except IOError as err:
        console.print(f"[ERROR] Can't load file:\n\t{err}", style=STYLE_FATAL)
    except MkdirError as err:
        console.print(f"[ERROR] Can't create directory:\n\t{err}", style=STYLE_FATAL)
    except UnicodeDecodeError as err:
        console.print(f"[ERROR] Input is not hex:\n\t{err}", style=STYLE_FATAL)
    else:
        return
    cleanup()
    raise typer.Exit(1)


def guess_key_length(text):
    fitnesses = calculate_fitnesses(text)
    if not fitnesses:
        raise AnalysisError("No candidates for key length found! Too small file?")

    print_fitnesses(fitnesses)
    guess_and_print_divisors(fitnesses)
    return get_max_fitnessed_key_length(fitnesses)


def print_fitnesses(fitnesses):
    console.print("The most probable key lengths:")

    fitnesses.sort(key=itemgetter(1), reverse=True)
    top10 = fitnesses[:10]
    best_fitness = top10[0][1]
    top10.sort(key=itemgetter(0))

    fitness_sum = calculate_fitness_sum(top10)
    width = len(str(max(i[0] for i in top10)))
    for key_length, fitness in top10:
        style_keylen = STYLE_BEST_KEYLEN if fitness == best_fitness else STYLE_KEYLEN
        style_prob = STYLE_BEST_PROB if fitness == best_fitness else STYLE_PROB
        pct = round(100 * fitness * 1.0 / fitness_sum, 1)
        console.print(f"{key_length:>{width}d}: ", style=style_keylen, end="")
        console.print(f"{pct:5.1f}%", style=style_prob)


def calculate_fitness_sum(fitnesses):
    return sum([f[1] for f in fitnesses])


def main():
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    typer.run(cli_main)
