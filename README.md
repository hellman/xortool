xortool.py
====================

A tool to do some xor analysis:

  - guess the key length (based on count of equal chars)
  - guess the key (base on knowledge of most frequent char)

**Notice:** xortool is now only running on Python 3. The old Python 2 version is accessible at the `py2` branch. The **pip** package has been updated.

Installation
---------------------

**xortool** can be installed using **pip**. The recommended way is to run the following command, which installs xortool only for current user. Remove the `--user` flag and run from root if global installation is preferred.

```bash
python3 -m pip install --user xortool
```


Usage
---------------------

```
xortool
  A tool to do some xor analysis:
  - guess the key length (based on count of equal chars)
  - guess the key (base on knowledge of most frequent char)

Usage:
  xortool [-x] [-m MAX-LEN] [-f] [-t CHARSET] [FILE]
  xortool [-x] [-l LEN] [-c CHAR | -b | -o] [-f] [-t CHARSET] [FILE]
  xortool [-x] [-m MAX-LEN| -l LEN] [-c CHAR | -b | -o] [-f] [-t CHARSET] [FILE]
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
```

Example 1
---------------------

```bash
# xor is xortool/xortool-xor
tests $ xor -f /bin/ls -s "secret_key" > binary_xored

tests $ xortool binary_xored
The most probable key lengths:
   2:   5.0%
   5:   8.7%
   8:   4.9%
  10:   15.4%
  12:   4.8%
  15:   8.5%
  18:   4.8%
  20:   15.1%
  25:   8.4%
  30:   14.9%
Key-length can be 5*n
Most possible char is needed to guess the key!

# 00 is the most frequent byte in binaries
tests $ xortool binary_xored -l 10 -c 00
...
1 possible key(s) of length 10:
secret_key

# decrypted ciphertexts are placed in ./xortool_out/Number_<key repr>
# ( have no better idea )
tests $ md5sum xortool_out/0_secret_key /bin/ls
29942e290876703169e1b614d0b4340a  xortool_out/0_secret_key
29942e290876703169e1b614d0b4340a  /bin/ls
```

The most common use is to pass just the encrypted file and the most frequent character (usually 00 for binaries and 20 for text files) - length will be automatically chosen:

```bash
tests $ xortool tool_xored -c 20
The most probable key lengths:
   2:   5.6%
   5:   7.8%
   8:   6.0%
  10:   11.7%
  12:   5.6%
  15:   7.6%
  20:   19.8%
  25:   7.8%
  28:   5.7%
  30:   11.4%
Key-length can be 5*n
1 possible key(s) of length 20:
an0ther s3cret \xdd key
```

Here, the key is longer then default 32 limit:

```bash
tests $ xortool ls_xored -c 00 -m 64
The most probable key lengths:
   3:   3.3%
   6:   3.3%
   9:   3.3%
  11:   7.0%
  22:   6.9%
  24:   3.3%
  27:   3.2%
  33:   18.4%
  44:   6.8%
  55:   6.7%
Key-length can be 3*n
1 possible key(s) of length 33:
really long s3cr3t k3y... PADDING
```

So, if automated decryption fails, you can calibrate:

- (`-m`) max length to try longer keys
- (`-l`) selected length to see some interesting keys
- (`-c`) the most frequent char to produce right plaintext

Example 2
---------------------

We are given a message in encoded in Base64 and XORed with an unknown key.

```bash
# xortool message.enc
The most probable key lengths:
   2:   12.3%
   4:   13.8%
   6:   10.5%
   8:   11.5%
  10:   8.6%
  12:   9.4%
  14:   7.1%
  16:   7.8%
  23:   10.4%
  46:   8.7%
Key-length can be 4*n
Most possible char is needed to guess the key!
```

We can now test the key lengths while filtering the outputs so that it only keeps the plaintexts holding the character set of Base64. After trying a few lengths, we come to the right one, which gives only 1 plaintext with a percentage of valid characters above the default threshold of 95%.

```bash
$ xortool message.enc -b -f -l 23 -t base64
256 possible key(s) of length 23:
\x01=\x121#"0\x17\x13\t\x7f ,&/\x12s\x114u\x170#
\x00<\x130"#1\x16\x12\x08~!-\'.\x13r\x105t\x161"
\x03?\x103! 2\x15\x11\x0b}".$-\x10q\x136w\x152!
\x02>\x112 !3\x14\x10\n|#/%,\x11p\x127v\x143
\x059\x165\'&4\x13\x17\r{$("+\x16w\x150q\x134\'
...
Found 1 plaintexts with 95.0%+ valid characters
See files filename-key.csv, filename-char_used-perc_valid.csv
```

By filtering the outputs on the character set of Base64, we directly keep the only solution.

Information
---------------------

Author: hellman

License: [MIT License](https://opensource.org/licenses/MIT)
