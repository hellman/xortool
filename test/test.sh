#!/usr/bin/env bash
# Usage:
#
# $ ./test/test.sh dist
# to test the (unbuilt) xortool from this dir
#
# $ ./test/test.sh
# to test the globally installed xortool

set -epux -o pipefail
shopt -s inherit_errexit

if [ $# -gt 0 ] && [ "dist" = "$1" ]; then
    export PATH="./xortool/:$PATH"
    export PYTHONPATH="."
fi

binary_xored_ok() {
    [ -d xortool_out ]
    grep -q "b'secret_key'" xortool_out/filename-key.csv
    grep -rc 'Free Software Foundation, Inc' xortool_out | \
        sed '/\.csv:/d;s/^[^:]*://;/^0$/d' | uniq -c | \
        egrep -q ' 1 1$'
}

binary_xored() {
    local f="$1"; shift

    hexdump -Cv "$f" |cut -s -d' ' -f 3-20 | \
    xortool --hex -b
    binary_xored_ok

    hexdump -Cv "$f" |cut -s -d' ' -f 3-20 | \
    xortool -x -l 10 -c 00
    binary_xored_ok

    rm -rf xortool_out
    ! xortool -x "$f"
    [ ! -d xortool_out ]

    rm -rf xortool_out
    ! xortool --hex "$f"
    [ ! -d xortool_out ]

    xortool -c 00 "$f"
    binary_xored_ok

    xortool --char=00 "$f"
    binary_xored_ok

    xortool -b "$f"
    binary_xored_ok

    xortool -b -l 10 "$f"
    binary_xored_ok

    xortool --brute-chars --key-length=10 "$f"
    binary_xored_ok

    xortool -c 00 --key-length=10 "$f"
    binary_xored_ok

    xortool -b --max-keylen=9 "$f"
    ! binary_xored_ok

    xortool -b --key-length=16 "$f"
    ! binary_xored_ok

    xortool -o "$f"
    ! binary_xored_ok

    xortool --brute-printable "$f"
    ! binary_xored_ok
}

ls_xored_ok() {
    [ -d xortool_out ]
    grep -q "b'really long s3cr3t k3y... PADDING'" xortool_out/filename-key.csv
    grep -qr 'Free Software Foundation, Inc' xortool_out
}

ls_xored() {
    local f="$1"; shift

    hexdump -Cv "$f" |cut -s -d' ' -f 3-20 | \
    xortool --hex -b
    ls_xored_ok

    hexdump -Cv "$f" |cut -s -d' ' -f 3-20 | \
    xortool -x -l 33 -c 00
    ls_xored_ok

    rm -rf xortool_out
    ! xortool -x "$f"
    [ ! -d xortool_out ]

    rm -rf xortool_out
    ! xortool --hex "$f"
    [ ! -d xortool_out ]

    xortool -c 00 "$f"
    ls_xored_ok
    xortool --char=00 "$f"
    ls_xored_ok

    xortool -b "$f"
    ls_xored_ok

    xortool -b -l 33 "$f"
    ls_xored_ok

    xortool --brute-chars --key-length=33 "$f"
    ls_xored_ok

    xortool -c 00 --key-length=33 "$f"
    ls_xored_ok

    xortool -b --max-keylen=32 "$f"
    ! ls_xored_ok

    xortool -b --key-length=35 "$f"
    ! ls_xored_ok

    xortool -o "$f"
    ! ls_xored_ok

    xortool --brute-printable "$f"
    ! ls_xored_ok
}

text_xored_ok() {
    [ -d xortool_out ]
    grep -q "b'"'\\xde\\xad\\xbe\\xef'"'" xortool_out/filename-key.csv
    grep -qr 'List of known bugs' xortool_out
}

text_xored() {
    xortool -o "$1"
    text_xored_ok

    xortool -o -t printable "$1"
    text_xored_ok

    xortool -o -t base32 "$1"
    text_xored_ok

    xortool -o -t base64 "$1"
    text_xored_ok

    xortool -o -t a "$1"
    text_xored_ok

    xortool -o -t A "$1"
    text_xored_ok

    xortool -o -t 1 "$1"
    text_xored_ok

    xortool -o -t '!' "$1"
    text_xored_ok

    xortool -o -t '*' "$1"
    text_xored_ok

    ! xortool -o -t Z "$1"

    xortool -o -t '' "$1"
    text_xored_ok
}

tool_xored_ok() {
    [ -d xortool_out ]
    grep -q "b'"'an0ther s3cret \\xdd key'"'" xortool_out/filename-key.csv
    grep -qr '# Author: hellman ( hellman1908@gmail.com )' xortool_out
}

tool_xored() {
    xortool -o "$1"
    tool_xored_ok
}

binary_xored test/data/binary_xored
ls_xored test/data/ls_xored
text_xored test/data/text_xored
tool_xored test/data/tool_xored

[ "$(./xortool/xortool-xor -n -s '\x3012345' -r 'A' | ./xortool/xortool-xor -r 'A' -f-)" = "012345" ]
[ "$(./xortool/xortool-xor -n -s '\x3012345' -r 'A')" = "qpsrut" ]
[ "$(./xortool/xortool-xor -n -h '30 31 32 33 34  35  ' -r 'A' | ./xortool/xortool-xor -r 'A' -f-)" = "012345" ]
[ "$(./xortool/xortool-xor -n -r qpsrut -r 'A')" = "012345" ]

xortool -c 00 --key-length=10 test/data/binary_xored
f_cmp="$(grep 'secret_key' xortool_out/filename-key.csv|cut -d\; -f1)"
xortool-xor -n -r secret_key -f "$f_cmp" | \
    cmp test/data/binary_xored
xortool-xor -n -r secret_key -f test/data/binary_xored | \
    cmp "$f_cmp"

echo OK
