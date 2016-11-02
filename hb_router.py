#!/usr/bin/env python
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from __future__ import print_function

# Python modules we need
import sys
from binascii import b2a_hex as h
from bitarray import bitarray
from time import time

# Debugging functions
from pprint import pprint

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet import task

# Things we import from the main hblink module
from hblink import CONFIG, HBMASTER, HBCLIENT, logger, systems, hex_str_3, int_id
import dec_dmr
import constants as const

# Import Bridging rules
# Note: A stanza *must* exist for any MASTER or CLIENT configured in the main
# configuration file and listed as "active". It can be empty, 
# but it has to exist.
try:
    from hb_routing_rules import RULES as RULES_FILE
    logger.info('Routing rules file found and rules imported')
except ImportError:
    sys.exit('Routing rules file not found or invalid')
    
# Convert integer GROUP ID numbers from the config into hex strings
# we need to send in the actual data packets.
for _system in RULES_FILE:
    RULES_FILE[_system]['GROUP_HANGTIME'] = RULES_FILE[_system]['GROUP_HANGTIME'] * 1000
    for _rule in RULES_FILE[_system]['GROUP_VOICE']:
        _rule['SRC_GROUP'] = hex_str_3(_rule['SRC_GROUP'])
        _rule['DST_GROUP'] = hex_str_3(_rule['DST_GROUP'])
        _rule['SRC_TS']    = _rule['SRC_TS']
        _rule['DST_TS']    = _rule['DST_TS']
        for i, e in enumerate(_rule['ON']):
            _rule['ON'][i] = hex_str_3(_rule['ON'][i])
        for i, e in enumerate(_rule['OFF']):
            _rule['OFF'][i] = hex_str_3(_rule['OFF'][i])
    if _system not in CONFIG['SYSTEMS']:
        sys.exit('ERROR: Routing rules found for system not configured main configuration')
for _system in CONFIG['SYSTEMS']:
    if _system not in RULES_FILE:
        sys.exit('ERROR: Routing rules not found for all systems configured')

RULES = RULES_FILE

# TEMPORARY DEBUGGING LINE -- TO BE REMOVED LATER
#pprint(RULES)

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Colin Durbridge, G4EML, Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'
__status__     = 'pre-alpha'


class routerMASTER(HBMASTER):
    
    def __init__(self, *args, **kwargs):
        HBMASTER.__init__(self, *args, **kwargs)
        
        self.ts1_state = {
            'LSTREAM_ID': '',
            'LPKT_TIME': time(),
            'LPKT_TYPE': const.HBPF_SLT_VTERM,
            'LSEQ_ID': 0x00,
            'LC': '',
            'EMBLC':  [0,0,0,0,0,0]
        }
        
        self.ts2_state = {
            'LSTREAM_ID': '',
            'LPKT_TIME': time(),
            'LPKT_TYPE': const.HBPF_SLT_VTERM,
            'LSEQ_ID': 0x00,
            'LC': '',
            'EMBLC':  [0,0,0,0,0,0]
        }
        

    def dmrd_received(self, _radio_id, _rf_src, _dst_id, _seq, _slot, _call_type, _frame_type, _dtype_vseq, _stream_id, _data):
        if _slot == 1:
            state = self.ts1_state
        elif _slot == 2:
            state = self.ts2_state
        else: 
            logger.error('(%s) DMRD received with invalid Timeslot value: %s', self._master, h(_data))
        pkt_time = time()
        dmrpkt = _data[20:54]
        
        if (_stream_id != state['LSTREAM_ID']) and ((state['LPKT_TYPE'] != const.HBPF_SLT_VTERM) or (pkt_time < state['LPKT_TIME'] + const.STREAM_TO)):
            logger.warning('(%s) Packet received <FROM> SUB: %s REPEATER: %s <TO> TGID %s, SLOT %s collided with existing call', self._master, int_id(_radio_id), int_id(_rf_src), int_id(_dst_id), _slot)
            return
        
        if (_stream_id != state['LSTREAM_ID']):
            logger.info('(%s) New call stream stareted <FROM> SUB: %s REPEATER: %s <TO> TGID %s, SLOT %s', self._master, int_id(_radio_id), int_id(_rf_src), int_id(_dst_id), _slot)
            state['LSTREAM_ID'] = _stream_id
            state['LPKT_TIME'] = pkt_time
            state['LSEQ_ID'] = _seq
            '''
            if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD:
                decoded = dec_dmr.voice_head_term(dmrpkt)
                state['LC'] = decoded['LC']
                print(h(state['LC']))
            '''
        if not state['LC'] and _frame_type == const.HBPF_VOICE:
            decoded = dec_dmr.voice(dmrpkt)
            state['EMBLC'][_dtype_vseq] = decoded['EMBED']
            print(h(decoded['EMBED']))
            
        if state['EMBLC'][1] and state['EMBLC'][2] and state['EMBLC'][3] and state['EMBLC'][4]:
            print(h(dec_dmr.bptc.decode_emblc(state['EMBLC'][1] + state['EMBLC'][2] + state['EMBLC'][3] + state['EMBLC'][4])))
            
                
        print(h(state['EMBLC'][1]),h(state['EMBLC'][2]),h(state['EMBLC'][3]),h(state['EMBLC'][4]))
            
        _bits = int_id(_data[15])
        if _call_type == 'group':
            
            _routed = False
            for rule in RULES[self._master]['GROUP_VOICE']:
                _target = rule['DST_NET']
                if (rule['SRC_GROUP'] == _dst_id and rule['SRC_TS'] == _slot and rule['ACTIVE'] == True):
                    if rule['SRC_TS'] != rule['DST_TS']:
                        _tmp_bits = _bits ^ 1 << 7
                    else:
                        _tmp_bits = _bits
                    _tmp_data = _data[:8] + rule['DST_GROUP'] + _data[11:15] + chr(_tmp_bits) + _data[16:]
                    #print(h(_data))
                    #print(h(_tmp_data))
                    systems[_target].send_system(_tmp_data)
                    _routed = True
                
                    logger.debug('(%s) Packet routed to %s system: %s', self._master, CONFIG['SYSTEMS'][_target]['MODE'], _target)
            if not _routed:
                logger.debug('(%s) Packet router no target TS/TGID %s/%s', self._master, _slot, int_id(_dst_id))

class routerCLIENT(HBCLIENT):
    
    def __init__(self, *args, **kwargs):
        HBCLIENT.__init__(self, *args, **kwargs)
        self.embeddec_lc_rx = {'B': '', 'C': '', 'D': '', 'E': '', 'F': ''}
        self.embeddec_lc_tx = {'B': '', 'C': '', 'D': '', 'E': '', 'F': ''}
    
    def dmrd_received(self, _radio_id, _rf_src, _dst_id, _seq, _slot, _call_type, _frame_type, _dtype_vseq, _stream_id, _data):
        _bits = int_id(_data[15])
        if _call_type == 'group':
            _routed = False
            for rule in RULES[self._client]['GROUP_VOICE']:
                _target = rule['DST_NET']
                if (rule['SRC_GROUP'] == _dst_id and rule['SRC_TS'] == _slot and rule['ACTIVE'] == True):
                    if rule['SRC_TS'] != rule['DST_TS']:
                        _tmp_bits = _bits ^ 1 << 7
                    else:
                        _tmp_bits = _bits
                    _tmp_data = _data[:8] + rule['DST_GROUP'] + _data[11:15] + chr(_bits) + _data[16:]
                    #print(h(_data))
                    #print(h(_tmp_data))
                    systems[_target].send_system(_tmp_data)
                    _routed = True
                    
                    logger.debug('(%s) Packet routed to %s system: %s', self._client, CONFIG['SYSTEMS'][_target]['MODE'], _target)
                
            if not _routed:
                logger.debug('(%s) Packet router no target TS/TGID %s/%s', self._client, _slot, int_id(_dst_id))

#************************************************
#      MAIN PROGRAM LOOP STARTS HERE
#************************************************

if __name__ == '__main__':
    logger.info('HBlink \'hb_router.py\' (c) 2016 N0MJS & the K0USY Group - SYSTEM STARTING...')
    
    # HBlink instance creation
    for system in CONFIG['SYSTEMS']:
        if CONFIG['SYSTEMS'][system]['ENABLED']:
            if CONFIG['SYSTEMS'][system]['MODE'] == 'MASTER':
                systems[system] = routerMASTER(system)
            elif CONFIG['SYSTEMS'][system]['MODE'] == 'CLIENT':
                systems[system] = routerCLIENT(system)     
            reactor.listenUDP(CONFIG['SYSTEMS'][system]['PORT'], systems[system], interface=CONFIG['SYSTEMS'][system]['IP'])
            logger.debug('%s instance created: %s, %s', CONFIG['SYSTEMS'][system]['MODE'], system, systems[system])

    reactor.run()