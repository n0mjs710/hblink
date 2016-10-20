#!/usr/bin/env python
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from __future__ import print_function
from bitarray import bitarray

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Jonathan Naylor, G4KLX'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'


def csum5(_data):
    _data = bytearray(_data)
    accum = 0
    assert len(_data) == 9, 'csum5 expected 9 bytes of data and got something else'
    
    for i in xrange(9):
        accum += _data[i]
    accum = chr(accum % 31)
    csum = bitarray()
    csum.frombytes(accum)
    del csum[0:3]

    return csum

 
    

if __name__ == '__main__':
    from binascii import b2a_hex as h
    
    message = '\x00\x10\x20\x00\x0c\x30\x2f\x9b\xe5'
    
    result = csum5(message)
    print(result, type(result))