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
        
        # Status information for the system, TS1 & TS2
        # 1 & 2 are "timeslot"
        # In TX_EMB_LC, 2-5 are burst B-E
        self.STATUS = {
            1: {
                'RX_STREAM_ID': '\x00',
                'TX_STREAM_ID': '\x00',
                'RX_TGID': '\x00',
                'TX_TGID': '\x00',
                'RX_TIME': time(),
                'TX_TIME': time(),
                'RX_TYPE': const.HBPF_SLT_VTERM,
                'RX_LC': '\x00',
                'TX_LC': '\x00',
                'TX_EMB_LC': {
                    2: '\x00',
                    3: '\x00',
                    4: '\x00',
                    5: '\x00',
                    }
                },
            2: {
                'RX_STREAM_ID': '\x00',
                'TX_STREAM_ID': '\x00',
                'RX_TGID': '\x00',
                'TX_TGID': '\x00',
                'RX_TIME': time(),
                'TX_TIME': time(),
                'RX_TYPE': const.HBPF_SLT_VTERM,
                'RX_LC': '\x00',
                'TX_LC': '\x00',
                'TX_EMB_LC': {
                    2: '\x00',
                    3: '\x00',
                    4: '\x00',
                    5: '\x00',
                    }
                }
            }

    def dmrd_received(self, _radio_id, _rf_src, _dst_id, _seq, _slot, _call_type, _frame_type, _dtype_vseq, _stream_id, _data):
        pkt_time = time()
        dmrpkt = _data[20:54]
        _bits = int_id(_data[15])

        if _call_type == 'group':
            
            # Is this a new call stream?   
            if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']):
                if ((self.STATUS[_slot]['RX_TYPE'] != const.HBPF_SLT_VTERM) or (pkt_time < self.STATUS[_slot]['RX_TIME'] + const.STREAM_TO)):
                    logger.warning('(%s) Packet received <FROM> SUB: %s REPEATER: %s <TO> TGID %s, SLOT %s collided with existing call', self._master, int_id(_rf_src), int_id(_radio_id), int_id(_dst_id), _slot)
                    return
                
                # This is a new call stream
                logger.info('(%s) Call stream START <FROM> SUB: %s REPEATER: %s <TO> TGID %s, SLOT %s', self._master, int_id(_rf_src), int_id(_radio_id), int_id(_dst_id), _slot)
                self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id
                self.STATUS[_slot]['RX_TIME'] = pkt_time
                self.STATUS[_slot]['RX_TGID'] = _dst_id
                
                # If we can, use the LC from the voice header as to keep all options intact
                if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD:
                    decoded = dec_dmr.voice_head_term(dmrpkt)
                    self.STATUS[_slot]['RX_LC'] = decoded['LC']
                
                # If we don't have a voice header then don't wait to decode it from the Embedded LC
                # just make a new one from the HBP header.
                else:
                    self.STATUS[_slot]['RX_LC'] = const.LC_OPT + _dst_id + _rf_src
        
            
            
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
                    logger.debug('(%s) Packet routed to %s system: %s', self._master, CONFIG['SYSTEMS'][_target]['MODE'], _target)
            
            
            
            # Final actions - Is this a voice terminator? and set the last packet type
            if (_frame_type == const.HBPF_DATA_SYNC) and (_dtype_vseq == const.HBPF_SLT_VTERM) and (self.STATUS[_slot]['RX_TYPE'] != const.HBPF_SLT_VTERM):
                self.STATUS[_slot]['LC'] = ''
                logger.info('(%s) Call stream END   <FROM> SUB: %s REPEATER: %s <TO> TGID %s, SLOT %s', self._master, int_id(_rf_src), int_id(_radio_id), int_id(_dst_id), _slot)
            self.STATE[_slot]['RX_TYPE'] = _dtype_vseq
                
                
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