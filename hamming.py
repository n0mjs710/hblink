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
def enc_15113(_data):
    csum = bitarray(4)
    csum[0] = _data[0] ^ _data[1] ^ _data[2] ^ _data[3] ^ _data[5] ^ _data[7] ^ _data[8]
    csum[1] = _data[1] ^ _data[2] ^ _data[3] ^ _data[4] ^ _data[6] ^ _data[8] ^ _data[9]
    csum[2] = _data[2] ^ _data[3] ^ _data[4] ^ _data[5] ^ _data[7] ^ _data[9] ^ _data[10]
    csum[3] = _data[0] ^ _data[1] ^ _data[2] ^ _data[4] ^ _data[6] ^ _data[7] ^ _data[10]
    return csum


#------------------------------------------------------------------------------
# Hamming 13,9,3 routines
#------------------------------------------------------------------------------

# ENCODER - returns a bitarray object containing the hamming checksums
def enc_1393(_data):
    csum = bitarray(4)
    csum[0] = _data[0] ^ _data[1] ^ _data[3] ^ _data[5] ^ _data[6]
    csum[1] = _data[0] ^ _data[1] ^ _data[2] ^ _data[4] ^ _data[6] ^ _data[7]
    csum[2] = _data[0] ^ _data[1] ^ _data[2] ^ _data[3] ^ _data[5] ^ _data[7] ^ _data[8]
    csum[3] = _data[0] ^ _data[2] ^ _data[4] ^ _data[5] ^ _data[8]
    return csum


#------------------------------------------------------------------------------
# Hamming 16,11,4 routines
#------------------------------------------------------------------------------

# ENCODER - returns a bitarray object containing the hamming checksums
def enc_16114(_data):
    assert len(_data) == 11, 'Hamming Encoder 16,11,4: Data not 11 bits long'
    csum = bitarray(5)
    csum[0] = _data[0] ^ _data[1] ^ _data[2] ^ _data[3] ^ _data[5] ^ _data[7] ^ _data[8]
    csum[1] = _data[1] ^ _data[2] ^ _data[3] ^ _data[4] ^ _data[6] ^ _data[8] ^ _data[9]
    csum[2] = _data[2] ^ _data[3] ^ _data[4] ^ _data[5] ^ _data[7] ^ _data[9] ^ _data[10]
    csum[3] = _data[0] ^ _data[1] ^ _data[2] ^ _data[4] ^ _data[6] ^ _data[7] ^ _data[10]
    csum[4] = _data[0] ^ _data[2] ^ _data[5] ^ _data[6] ^ _data[8] ^ _data[9] ^ _data[10]
    return csum