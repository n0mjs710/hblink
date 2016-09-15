#!/usr/bin/env python
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from __future__ import print_function

from bitstring import BitArray

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Jonathan Naylor, G4KLX; Ian Wraith'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'


def binary_196(_data):
    _data = bytearray(_data)
    _data = BitArray(_data)
    return _data[:98] + _data[-98:]
    
def deint_196(_data):
    deint = BitArray(196)
    for index in range(196):
        deint[index] = _data[(index * 181) % 196]
    return deint
    
def extract_196(_data):
    databits = BitArray()
    databits.append(_data[4:12])
    databits.append(_data[16:27])
    databits.append(_data[31:42])
    databits.append(_data[46:57])
    databits.append(_data[61:72])
    databits.append(_data[76:87])
    databits.append(_data[91:102])
    databits.append(_data[106:117])
    databits.append(_data[121:132])
    return databits.tobytes()
    

if __name__ == '__main__':
    
    from binascii import b2a_hex as h
    
    # Validation Example
    data = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20'
    
    bin_data = binary_196(data)
    deint_data = deint_196(bin_data)
    ext_data = extract_196(deint_data)
    
    print('original 33 byte data block:')
    print(h(data))
    print(len(data))
    print()
    
    print('binary data (discarding sync)')
    print(bin_data.len)
    print(bin_data)
    print()

    print('deinterleaved binary data')
    print(deint_data.len)
    print(deint_data)
    print()

    print('decoded hex data')
    print(len(ext_data)*8)
    print(h(ext_data))