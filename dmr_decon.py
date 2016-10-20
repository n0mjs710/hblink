#!/usr/bin/env python
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from __future__ import print_function

from bitarray import bitarray
import bptc
import constants as const

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Jonathan Naylor, G4KLX; Ian Wraith'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'

def to_bits(_string):
    _bits = bitarray(endian='big')
    _bits.frombytes(_string)
    return _bits

# Returns useable LC data - 9 bytes info + 3 bytes RS(12,9) ECC
def lc_data_12(_data):
    return _data[4:12]+_data[16:27]+_data[31:42]+_data[46:57]+_data[61:72]+_data[76:87]+_data[91:102]+_data[106:117]+_data[121:132]
    
# Returns useable LC data - 9 bytes info, no ECC
def lc_data_9(_data):
    return _data[4:12]+_data[16:27]+_data[31:42]+_data[46:57]+_data[61:72]+_data[76:87]+_data[91:100]


def voice_head_term(_string):
    burst = to_bits(_string)
    info = burst[0:98] + burst[166:264]
    de_int_info = bptc.deinterleave_19696(info)    
    slot_type = burst[98:108] + burst[156:166]
    lc = to_bytes(lc_data_9(de_int_info))
    cc = to_bytes(slot_type[0:4])
    dtype = to_bytes(slot_type[4:8])
    return (lc, cc, dtype)


def voice_sync(_string):
    burst = to_bits(_string)
    ambe = [0,0,0]
    ambe[0] = burst[0:72]
    ambe[1] = burst[72:108] + burst[156:192]
    ambe[2] = burst[192:264]
    return (ambe)
    
    
def voice(_string):
    burst = to_bits(_string)
    ambe = [0,0,0]
    ambe[0] = burst[0:72]
    ambe[1] = burst[72:108] + burst[156:192]
    ambe[2] = burst[192:264]
    emb = burst[108:116] + burst[148:156]
    embeded = burst[116:148]
    cc = (emb[0:4])
    # pi = (emb[4:5])
    lcss = (emb[5:7])
    return (ambe, cc, lcss, embeded)


def to_bytes(_bits):
    add_bits = 8 - (len(_bits) % 8)
    if add_bits < 8:
        for bit in xrange(add_bits):
            _bits.insert(0,0)
    _string =  _bits.tobytes()
    return _string



#------------------------------------------------------------------------------
# Used to execute the module directly to run built-in tests
#------------------------------------------------------------------------------

if __name__ == '__main__':
    
    from binascii import b2a_hex as h
    from time import time
    
    # SAMPLE, KNOWN GOOD DMR BURSTS
    data_head  = '\x2b\x60\x04\x10\x1f\x84\x2d\xd0\x0d\xf0\x7d\x41\x04\x6d\xff\x57\xd7\x5d\xf5\xde\x30\x15\x2e\x20\x70\xb2\x0f\x80\x3f\x88\xc6\x95\xe2'    
    voice_a    = '\xb9\xe8\x81\x52\x61\x73\x00\x2a\x6b\xb9\xe8\x81\x52\x67\x55\xfd\x7d\xf7\x5f\x71\x73\x00\x2a\x6b\xb9\xe8\x81\x52\x61\x73\x00\x2a\x6a'
    voice_b    = '\xb9\xe8\x81\x52\x61\x73\x00\x2a\x6b\xb9\xe8\x81\x52\x61\x34\xe0\xf0\x60\x69\x11\x73\x00\x2a\x6b\xb9\xe8\x81\x52\x61\x73\x00\x2a\x6a'
    voice_c    = '\xb9\xe8\x81\x52\x61\x73\x00\x2a\x6b\xb9\xe8\x81\x52\x61\x71\x71\x10\x04\x77\x41\x73\x00\x2a\x6b\xb9\xe8\x81\x52\x61\x73\x00\x2a\x6a'
    voice_d    = '\xb9\xe8\x81\x52\x61\x73\x00\x2a\x6b\x95\x4b\xe6\x50\x01\x70\xc0\x31\x81\xb7\x43\x10\xb0\x07\x77\xa6\xc6\xcb\x53\x73\x27\x89\x48\x3a'
    voice_e    = '\x86\x5a\xe7\x61\x75\x55\xb5\x06\x01\xb7\x58\xe6\x65\x11\x51\x75\xa0\xf4\xe0\x71\x24\x81\x50\x01\xff\xf5\xa3\x37\x70\x61\x28\xa7\xca'
    voice_f    = '\xee\xe7\x81\x75\x74\x61\x4d\xf2\xff\xcc\xf4\xa0\x55\x11\x10\x00\x00\x00\x0e\x24\x30\x59\xe7\xf9\xe9\x08\xa0\x75\x62\x02\xcc\xd6\x22'
    voice_term = '\x2b\x0f\x04\xc4\x1f\x34\x2d\xa8\x0d\x80\x7d\xe1\x04\xad\xff\x57\xd7\x5d\xf5\xd9\x65\x01\x2d\x18\x77\xd2\x03\xc0\x37\x88\xdf\x95\xd1'
    
    
    print('Header Validation:')
    t0 = time()
    lc = voice_head_term(data_head)
    t1 = time()
    print(h(lc[0]), h(lc[1]), h(lc[2]))
    print(t1-t0, '\n')
    
    print('Voice Burst A Validation:')
    t0 = time()
    lc = voice_sync(voice_a)
    t1 = time()
    print(lc[0])
    print(t1-t0, '\n')
    
    print('Voice Burst B Validation:')
    t0 = time()
    lc = voice(voice_b)
    t1 = time()
    print(lc[0], h(lc[1]), h(lc[2]), lc[3])
    print(t1-t0, '\n')
    
    print('Voice Burst C Validation:')
    t0 = time()
    lc = voice(voice_c)
    t1 = time()
    print(lc[0], h(lc[1]), h(lc[2]), lc[3])
    print(t1-t0, '\n')
    
    print('Voice Burst D Validation:')
    t0 = time()
    lc = voice(voice_d)
    t1 = time()
    print(lc[0], h(lc[1]), h(lc[2]), lc[3])
    print(t1-t0, '\n')
    
    print('Voice Burst E Validation:')
    t0 = time()
    lc = voice(voice_e)
    t1 = time()
    print(lc[0], h(lc[1]), h(lc[2]), lc[3])
    print(t1-t0, '\n')
    
    print('Voice Burst F Validation:')
    t0 = time()
    lc = voice(voice_f)
    t1 = time()
    print(lc[0], h(lc[1]), h(lc[2]), lc[3])
    print(t1-t0, '\n')
    
    print('Terminator Validation:')
    t0 = time()
    lc = voice_head_term(voice_term)
    t1 = time()
    print(h(lc[0]), h(lc[1]), h(lc[2]))
    print(t1-t0)