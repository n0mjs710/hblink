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


#------------------------------------------------------------------------------
# Hamming 15,11,3 routines
#------------------------------------------------------------------------------

# ENCODER- returns a bitarray object containing the hamming checksums
def enc_hamming_15113(_data):
    csum = bitarray(4)
    csum[0] = _data[0] ^ _data[1] ^ _data[2] ^ _data[3] ^ _data[5] ^ _data[7] ^ _data[8]
    csum[1] = _data[1] ^ _data[2] ^ _data[3] ^ _data[4] ^ _data[6] ^ _data[8] ^ _data[9]
    csum[2] = _data[2] ^ _data[3] ^ _data[4] ^ _data[5] ^ _data[7] ^ _data[9] ^ _data[10]
    csum[3] = _data[0] ^ _data[1] ^ _data[2] ^ _data[4] ^ _data[6] ^ _data[7] ^ _data[10]
    return csum

# DECODER - Returns a tuple of (decoded data, True if an error was corrected)
def dec_hamming_15113(_data):
    chk0 = _data[0] ^ _data[1] ^ _data[2] ^ _data[3] ^ _data[5] ^ _data[7] ^ _data[8]
    chk1 = _data[1] ^ _data[2] ^ _data[3] ^ _data[4] ^ _data[6] ^ _data[8] ^ _data[9]
    chk2 = _data[2] ^ _data[3] ^ _data[4] ^ _data[5] ^ _data[7] ^ _data[9] ^ _data[10]
    chk3 = _data[0] ^ _data[1] ^ _data[2] ^ _data[4] ^ _data[6] ^ _data[7] ^ _data[10]
    
    n = 0
    error = False
    
    n |=  0x01 if chk0 != _data[11] else 0x00
    n |=  0x02 if chk1 != _data[12] else 0x00
    n |=  0x04 if chk2 != _data[13] else 0x00
    n |=  0x08 if chk3 != _data[14] else 0x00
    
    if n == 0x01: _data[11] = not _data[11]; return (_data, True)
    if n == 0x02: _data[12] = not _data[12]; return (_data, True)
    if n == 0x04: _data[13] = not _data[13]; return (_data, True)
    if n == 0x08: _data[14] = not _data[14]; return (_data, True)
    
    if n == 0x0f: _data[0]  = not _data[0];  return (_data, True)
    if n == 0x07: _data[1]  = not _data[1];  return (_data, True)
    if n == 0x0b: _data[2]  = not _data[2];  return (_data, True)
    if n == 0x03: _data[3]  = not _data[3];  return (_data, True)
    if n == 0x0d: _data[4]  = not _data[4];  return (_data, True)
    if n == 0x05: _data[5]  = not _data[5];  return (_data, True)
    if n == 0x09: _data[6]  = not _data[6];  return (_data, True)
    if n == 0x0e: _data[7]  = not _data[7];  return (_data, True)
    if n == 0x06: _data[8]  = not _data[8];  return (_data, True)
    if n == 0x0a: _data[9]  = not _data[9];  return (_data, True)
    if n == 0x0c: _data[10] = not _data[10]; return (_data, True)
    
    return (_data, False)


#------------------------------------------------------------------------------
# Hamming 13,9,3 routines
#------------------------------------------------------------------------------

# ENCODER - returns a bitarray object containing the hamming checksums
def enc_hamming_1393(_data):
    csum = bitarray(4)
    csum[0] = _data[0] ^ _data[1] ^ _data[3] ^ _data[5] ^ _data[6]
    csum[1] = _data[0] ^ _data[1] ^ _data[2] ^ _data[4] ^ _data[6] ^ _data[7]
    csum[2] = _data[0] ^ _data[1] ^ _data[2] ^ _data[3] ^ _data[5] ^ _data[7] ^ _data[8]
    csum[3] = _data[0] ^ _data[2] ^ _data[4] ^ _data[5] ^ _data[8]
    return csum

# DECODER  - Returns a tuple of (decoded data, True if an error was corrected)
def dec_hamming_1393(_data):
    chk0 = _data[0] ^ _data[1] ^ _data[3] ^ _data[5] ^ _data[6]
    chk1 = _data[0] ^ _data[1] ^ _data[2] ^ _data[4] ^ _data[6] ^ _data[7]
    chk2 = _data[0] ^ _data[1] ^ _data[2] ^ _data[3] ^ _data[5] ^ _data[7] ^ _data[8]
    chk3 = _data[0] ^ _data[2] ^ _data[4] ^ _data[5] ^ _data[8]
    
    n = 0
    error = False
    
    n |=  0x01 if chk0 != _data[9]  else 0x00
    n |=  0x02 if chk1 != _data[10] else 0x00
    n |=  0x04 if chk2 != _data[11] else 0x00
    n |=  0x08 if chk3 != _data[12] else 0x00
    
    if n == 0x01: _data[9]  = not _data[9];  return (_data, True)
    if n == 0x02: _data[10] = not _data[10]; return (_data, True)
    if n == 0x04: _data[11] = not _data[11]; return (_data, True)
    if n == 0x08: _data[12] = not _data[12]; return (_data, True)
    
    if n == 0x0f: _data[0]  = not _data[0];  return (_data, True)
    if n == 0x07: _data[1]  = not _data[1];  return (_data, True)
    if n == 0x0b: _data[2]  = not _data[2];  return (_data, True)
    if n == 0x03: _data[3]  = not _data[3];  return (_data, True)
    if n == 0x0d: _data[4]  = not _data[4];  return (_data, True)
    if n == 0x05: _data[5]  = not _data[5];  return (_data, True)
    if n == 0x09: _data[6]  = not _data[6];  return (_data, True)
    if n == 0x0e: _data[7]  = not _data[7];  return (_data, True)
    if n == 0x06: _data[8]  = not _data[8];  return (_data, True)
    
    return (_data, False)


#------------------------------------------------------------------------------
# Used to execute the module directly to run built-in tests
#------------------------------------------------------------------------------

if __name__ == '__main__':
    
    # Validation Example
    
    raw_data = '\x44\x4d\x52\x44\x00\x2f\x9b\xe5\x00\x0c\x30\x00\x04\xc2\xc4\xa1\xa1\x99\x48\x6e\x2b\x60\x04\x10\x1f\x84\x2d\xd0\x0d\xf0\x7d\x41\x04\x6d\xff\x57\xd7\x5d\xf5\xde\x30\x15\x2e\x20\x70\xb2\x0f\x80\x3f\x88\xc6\x95\xe2\x00\x00'
    raw_data = raw_data[20:53]
    
    data = bitarray(endian='big')
    data.frombytes('raw_data')
    data = data[4:]
    
    print(data[0:11], data[11:15])
    print(dec_hamming_15113(data[0:15])[0][0:11], dec_hamming_15113(data[0:15])[0][11:15], dec_hamming_15113(data[0:15])[1])
    print(enc_hamming_15113(data[0:11]))
    print()
    print(data[0:9], data[9:13])
    print(dec_hamming_1393(data[0:13])[0][0:9], dec_hamming_1393(data[0:13])[0][9:13], dec_hamming_15113(data[0:15])[1])
    print(enc_hamming_1393(data[0:9]))