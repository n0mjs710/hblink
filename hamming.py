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
    
    if n == 0x09: _data[0]  = not _data[0];  return (_data, True)
    if n == 0x0b: _data[1]  = not _data[1];  return (_data, True)
    if n == 0x0f: _data[2]  = not _data[2];  return (_data, True)
    if n == 0x07: _data[3]  = not _data[3];  return (_data, True)
    if n == 0x0e: _data[4]  = not _data[4];  return (_data, True)
    if n == 0x05: _data[5]  = not _data[5];  return (_data, True)
    if n == 0x0a: _data[6]  = not _data[6];  return (_data, True)
    if n == 0x0d: _data[7]  = not _data[7];  return (_data, True)
    if n == 0x03: _data[8]  = not _data[8];  return (_data, True)
    if n == 0x06: _data[9]  = not _data[9];  return (_data, True)
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
    
    # Good
    _data = bitarray('0000000000000000000100000011101000000000000000000000110001110011000000100100111110011010110111100101111001011010110101101100010110100110000110000111100111010011101101000010101001110000100101010100')
    # Bad
    _data = bitarray('0000000000000000000110000011101000000000000000000000110001110011000000100100111110011010110111100101111001011010110101101100010110100110000110000111100111010011101101000010101001110000100101010100')

    rows = (_data[1:16],_data[16:31],_data[31:46],_data[46:61],_data[61:76],_data[76:91],_data[91:106],_data[106:121],_data[121:136])
    
    for row in rows:
        print('original data:', row[0:11], 'original parity:', row[11:15])
        
        hamming_dec = dec_hamming_15113(row[0:15])
        code = hamming_dec[0]
        error = hamming_dec[1]
    
        print('return data:  ', code[0:11], 'return parity:  ', code[11:15], 'return error:', error)
        print('calculated parity:', enc_hamming_15113(row[0:11]))
        print()