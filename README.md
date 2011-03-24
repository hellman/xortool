xortool.py
====================

A tool to do some xor analysis:

  - guess the key length (based on count of equal chars)
  - guess the key (base on knowledge of most frequent char)

Usage
---------------------

<pre>
  xortool [-h|--help] [OPTIONS] [<filename>]
Options:
  -l,--key-length     length of the key
  -c,--char           most frequent char
  -x,--hex            input is hex-encoded str
  -m,--max-keylen     maximum key length to probe
</pre>

Example
---------------------

<blockquote><pre>
# xor is some external script to encrypt files
tests $ xor -f /bin/ls -s "s3cret \xa9 keyS" > binary_xored 

tests $ python ../xortool.py binary_xored
Probable key lengths:
   2:   5.0 %
   5:   8.7 %
   8:   4.9 %
  10:   15.4 %
  12:   4.8 %
  15:   8.5 %
  18:   4.8 %
  20:   15.1 %
  22:   4.7 %
  25:   8.4 %
  28:   4.7 %
  30:   14.9 %
Key-length can be 5*n
Most possible char is needed to guess the key!

# 00 is the most frequent byte in binaries
tests $ python ../xortool.py binary_xored -l 10 -c 00
...
1 possible key(s) of length 10:
secret_key

# decrypted ciphertexts are placed in ./xortool/Number_<key repr>
# ( have no better idea )
tests $ md5sum xortool/0_secret_key /bin/ls
29942e290876703169e1b614d0b4340a  xortool/0_secret_key
29942e290876703169e1b614d0b4340a  /bin/ls
</pre></blockquote>

The most common use is just pass the encrypted file and
the most frequent character (usually 00 for binaries and 20 for text files):

<blockquote><pre>
tests $ xortool tool_xored -c 20
Probable key lengths:
   2:   5.6 %
   5:   7.8 %
   8:   6.0 %
  10:   11.7 %
  12:   5.6 %
  15:   7.6 %
  18:   5.4 %
  20:   19.8 %
  22:   5.4 %
  25:   7.8 %
  28:   5.7 %
  30:   11.4 %
Key-length can be 5*n
1 possible key(s) of length 20:
an0ther s3cret \xdd key
</pre></blockquote>

Author: hellman ( hellman1908@gmail.com )
License: GNU General Public License v2 (http://opensource.org/licenses/gpl-2.0.php)
