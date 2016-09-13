from __future__ import print_function

from bitstring import BitArray
from binascii import b2a_hex as h

raw_data = BitArray(196)
de_interleaved = BitArray(196)

test = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a'

def to_int(_hex_string):
    return int(h(_hex_string), 16)

def decode(_data):
    pass
    
def extract_binary(_data):
    _data = to_int(_data)
    _data = BitArray(_data)
    print(_data)    

print(h(test))
extract_binary(test)