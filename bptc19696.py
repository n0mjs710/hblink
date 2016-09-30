#!/usr/bin/env python
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from __future__ import print_function
from bitarray import bitarray
import hamming

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Jonathan Naylor, G4KLX; Ian Wraith'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'


#------------------------------------------------------------------------------
# Interleaver Index
#------------------------------------------------------------------------------

INDEX_181 = (
0, 181, 166, 151, 136, 121, 106, 91, 76, 61, 46, 31, 16, 1, 182, 167, 152, 137,
122, 107, 92, 77, 62, 47, 32, 17, 2, 183, 168, 153, 138, 123, 108, 93, 78, 63,
48, 33, 18, 3, 184, 169, 154, 139, 124, 109, 94, 79, 64, 49, 34, 19, 4, 185, 170,
155, 140, 125, 110, 95, 80, 65, 50, 35, 20, 5, 186, 171, 156, 141, 126, 111, 96,
81, 66, 51, 36, 21, 6, 187, 172, 157, 142, 127, 112, 97, 82, 67, 52, 37, 22, 7,
188, 173, 158, 143, 128, 113, 98, 83, 68, 53, 38, 23, 8, 189, 174, 159, 144, 129,
114, 99, 84, 69, 54, 39, 24, 9, 190, 175, 160, 145, 130, 115, 100, 85, 70, 55, 40,
25, 10, 191, 176, 161, 146, 131, 116, 101, 86, 71, 56, 41, 26, 11, 192, 177, 162,
147, 132, 117, 102, 87, 72, 57, 42, 27, 12, 193, 178, 163, 148, 133, 118, 103, 88,
73, 58, 43, 28, 13, 194, 179, 164, 149, 134, 119, 104, 89, 74, 59, 44, 29, 14,
195, 180, 165, 150, 135, 120, 105, 90, 75, 60, 45, 30, 15)


#------------------------------------------------------------------------------
# BPTC(196,96) Decoding Routings
#------------------------------------------------------------------------------

# Converts a DMR frame using 98-68-98 (info-sync/EMB-info) into 196 bit array
# Applies interleave indecies de-interleave 196 bit array
def deinterleave_19696(_data):
    _bits = bitarray(endian='big')
    _bits.frombytes(_data)
    for i in xrange(68):
        _bits.pop(98)
    deint = bitarray(196, endian='big')
    for index in xrange(196):
        deint[index] = _bits[INDEX_181[index]]  # the real math is slower: deint[index] = _data[(index * 181) % 196]
    return deint

# Applies BTPC error detection/correction routines
# This routine, in practice, will not be used in HBlink or DMRlink - it's only usefull for OTA direct data
def error_check_19696(_data):
    count = 0
    column = bitarray(13, endian='big')
    
    while True:
        errors = False
        for col in xrange(15):
            pos = col + 1
            for index in xrange(13):
                column[index] = _data[pos]
                pos += 15
            
            result_1393 = hamming.dec_1393(column)
            if result_1393[1]:
                pos = col + 1
                for index in xrange(13):
                    _data[pos] = result_1393[0][index]
                    pos += 15
                errors = True
                
        for index in xrange(9):
            pos = (index*15) + 1
            result_15113 = hamming.dec_15113(_data[pos:(pos+15)])
            if result_15113[1]:
                errors = True
                _data[pos:(pos+15)] = result_15113[0]
        
        count += 1
        if not errors or count > 4: break
    return (errors)
    
# Returns useable LC data - 9 bytes info + 3 bytes RS(12,9) ECC
def to_bytes_19696(_data):
    databits = _data[4:12]+_data[16:27]+_data[31:42]+_data[46:57]+_data[61:72]+_data[76:87]+_data[91:102]+_data[106:117]+_data[121:132]
    return databits.tobytes()


#------------------------------------------------------------------------------
# BPTC(196,96) Encoding Routings
#------------------------------------------------------------------------------

def interleave_19696(_data):
    inter = bitarray(196, endian='big')
    for index in xrange(196):
        inter[INDEX_181[index]] = _data[index]  # the real math is slower: deint[index] = _data[(index * 181) % 196]
    return inter

# Accepts 12 byte LC header + RS1293, converts to binary and pads for 196 bit
# encode hamming 15113 to rows and 1393 to columns
def enc_bptc_19696(_data):
    # Create a bitarray from the 4 bytes of LC data (includes RS1293 ECC)
    _bdata = bitarray(endian='big')
    _bdata.frombytes(_data)
    
    # Insert R0-R3 bits
    for i in xrange(4):
        _bdata.insert(0, 0)
    
    # Get row hamming 15,11,3 and append. +1 is to account for R3 that makes an even 196bit string
    for index in xrange(9):
        spos = (index*15) + 1
        epos= spos + 11
        _rowp = hamming.enc_15113(_bdata[spos:epos])
        for pbit in xrange(4):
            _bdata.insert(epos+pbit,_rowp[pbit])
    
    # Get column hamming 13,9,3 and append. +1 is to account for R3 that makes an even 196bit string
    # Pad out the bitarray to a full 196 bits. Can't insert into 'columns'
    for i in xrange(60):
        _bdata.append(0)
    
    column = bitarray(9, endian='big')  # Temporary bitarray to hold column data
    for col in xrange(15):
        spos = col + 1
        for index in xrange(9):
            column[index] = _bdata[spos]
            spos += 15
        _colp = hamming.enc_1393(column)
        
        # Insert bits into matrix...
        cpar = 136 + col                # Starting location in the matrix for column bits
        for pbit in xrange(4):
            _bdata[cpar] =  _colp[pbit]
            cpar += 15

    return _bdata
    
    
#------------------------------------------------------------------------------
# Used to execute the module directly to run built-in tests
#------------------------------------------------------------------------------

if __name__ == '__main__':
    
    from binascii import b2a_hex as h
    from time import time

    # Validation Example
    
    orig_data = '\x00\x10\x20\x00\x0c\x30\x2f\x9b\xe5\xda\xd4\x5a'
    t0 = time()
    enc_data = enc_bptc_19696(orig_data)
    inter_data = interleave_19696(enc_data)
    t1 = time()
    encode_time = t1-t0
    
    # Good Data
    dec_data = '\x2b\x60\x04\x10\x1f\x84\x2d\xd0\x0d\xf0\x7d\x41\x04\x6d\xff\x57\xd7\x5d\xf5\xde\x30\x15\x2e\x20\x70\xb2\x0f\x80\x3f\x88\xc6\x95\xe2'
    # Bad Data
    #dec_data = '\x2b\x60\xff\xff\xff\x85\x2d\xd0\x0d\xf0\x7d\x41\x04\x6d\xff\x57\xd7\x5d\xf5\xde\x30\x15\x2e\x20\x70\xb2\x0f\x80\x3f\x88\xc6\x95\xe2'
    
    t0 = time()
    deint_data = deinterleave_19696(dec_data)
    err_corrected = error_check_19696(deint_data) # This corrects deint_data in place -- it does not return a new array!!!
    ext_data = to_bytes_19696(deint_data)
    t1 = time()
    decode_time = t1-t0
    
    
    print('VALIDATION ROUTINE:')
    print()
    print('ENCODER TEST:')
    print('Original Data: {}, {} bytes'.format(h(orig_data), len(orig_data)))
    print('Encoding time: {} seconds'.format(encode_time))
    print('Encoded data:  {}, {} bits'.format(enc_data, len(enc_data)))
    print()
    print('DECODER TEST:')
    print('Encoded data:  {}, {} bytes'.format(h(dec_data), len(dec_data)))
    print('Decoding Time: {} seconds'.format(t1-t0))
    if err_corrected:
        print('WARNING DATA COULD NOT BE CORRECTED')
    else:
        print('Decoded Data:  {}, {} bytes'.format(h(ext_data), len(ext_data)))
    print()
    
    print('ENCODED vs. DECODED:')
    print('enc:', enc_data)
    print('dec:', deint_data)
    print(enc_data == deint_data)