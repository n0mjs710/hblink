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
from hblink import CONFIG, HBSYSTEM, logger, systems, hex_str_3, int_id, sub_alias, peer_alias, tg_alias
import dec_dmr
import bptc
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
    for _rule in RULES_FILE[_system]['GROUP_VOICE']:
        _rule['SRC_GROUP'] = hex_str_3(_rule['SRC_GROUP'])
        _rule['DST_GROUP'] = hex_str_3(_rule['DST_GROUP'])
        _rule['SRC_TS']    = _rule['SRC_TS']
        _rule['DST_TS']    = _rule['DST_TS']
        for i, e in enumerate(_rule['ON']):
            _rule['ON'][i] = hex_str_3(_rule['ON'][i])
        for i, e in enumerate(_rule['OFF']):
            _rule['OFF'][i] = hex_str_3(_rule['OFF'][i])
        _rule['TIMEOUT']= _rule['TIMEOUT']*60
        _rule['TIMER']      = time() + _rule['TIMEOUT']
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
__credits__    = 'Colin Durrouting, G4EML, Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'
__status__     = 'pre-alpha'


# Run this every minute for rule timer updates
def rule_timer_loop():
    logger.info('(ALL HBSYSTEMS) Rule timer loop started')
    _now = time()
    for _system in RULES:
        for _rule in RULES[_system]['GROUP_VOICE']:
            if _rule['TO_TYPE'] == 'ON':
                if _rule['ACTIVE'] == True:
                    if _rule['TIMER'] < _now:
                        _rule['ACTIVE'] = False
                        logger.info('(%s) Rule timout DEACTIVATE: Rule name: %s, Target HBSystem: %s, TS: %s, TGID: %s', _system, _rule['NAME'], _rule['DST_NET'], _rule['DST_TS']+1, int_id(_rule['DST_GROUP']))
                    else:
                        timeout_in = _rule['TIMER'] - _now
                        logger.info('(%s) Rule ACTIVE with ON timer running: Timeout eligible in: %ds, Rule name: %s, Target HBSystem: %s, TS: %s, TGID: %s', _system, timeout_in, _rule['NAME'], _rule['DST_NET'], _rule['DST_TS']+1, int_id(_rule['DST_GROUP']))
            elif _rule['TO_TYPE'] == 'OFF':
                if _rule['ACTIVE'] == False:
                    if _rule['TIMER'] < _now:
                        _rule['ACTIVE'] = True
                        logger.info('(%s) Rule timout ACTIVATE: Rule name: %s, Target HBSystem: %s, TS: %s, TGID: %s', _system, _rule['NAME'], _rule['DST_NET'], _rule['DST_TS']+1, int_id(_rule['DST_GROUP']))
                    else:
                        timeout_in = _rule['TIMER'] - _now
                        logger.info('(%s) Rule DEACTIVE with OFF timer running: Timeout eligible in: %ds, Rule name: %s, Target HBSystem: %s, TS: %s, TGID: %s', _system, timeout_in, _rule['NAME'], _rule['DST_NET'], _rule['DST_TS']+1, int_id(_rule['DST_GROUP']))
            else:
                logger.debug('Rule timer loop made no rule changes')


class routerSYSTEM(HBSYSTEM):
    
    def __init__(self, *args, **kwargs):
        HBSYSTEM.__init__(self, *args, **kwargs)
        
        # Status information for the system, TS1 & TS2
        # 1 & 2 are "timeslot"
        # In TX_EMB_LC, 2-5 are burst B-E
        self.STATUS = {
            1: {
                'RX_START':     time(),
                'RX_SEQ':       '\x00',
                'RX_RFS':       '\x00',
                'TX_RFS':       '\x00',
                'RX_STREAM_ID': '\x00',
                'TX_STREAM_ID': '\x00',
                'RX_TGID':      '\x00\x00\x00',
                'TX_TGID':      '\x00\x00\x00',
                'RX_TIME':      time(),
                'TX_TIME':      time(),
                'RX_TYPE':      const.HBPF_SLT_VTERM,
                'RX_LC':        '\x00',
                'TX_H_LC':      '\x00',
                'TX_T_LC':      '\x00',
                'TX_EMB_LC': {
                    1: '\x00',
                    2: '\x00',
                    3: '\x00',
                    4: '\x00',
                    }
                },
            2: {
                'RX_START':     time(),
                'RX_SEQ':       '\x00',
                'RX_RFS':       '\x00',
                'TX_RFS':       '\x00',
                'RX_STREAM_ID': '\x00',
                'TX_STREAM_ID': '\x00',
                'RX_TGID':      '\x00\x00\x00',
                'TX_TGID':      '\x00\x00\x00',
                'RX_TIME':      time(),
                'TX_TIME':      time(),
                'RX_TYPE':      const.HBPF_SLT_VTERM,
                'RX_LC':        '\x00',
                'TX_H_LC':      '\x00',
                'TX_T_LC':      '\x00',
                'TX_EMB_LC': {
                    1: '\x00',
                    2: '\x00',
                    3: '\x00',
                    4: '\x00',
                    }
                }
            }

    def dmrd_received(self, _radio_id, _rf_src, _dst_id, _seq, _slot, _call_type, _frame_type, _dtype_vseq, _stream_id, _data):
        pkt_time = time()
        dmrpkt = _data[20:53]
        _bits = int_id(_data[15])

        if _call_type == 'group':
            
            # Is this a new call stream?   
            if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']):
                if (self.STATUS[_slot]['RX_TYPE'] != const.HBPF_SLT_VTERM) and (pkt_time < (self.STATUS[_slot]['RX_TIME'] + const.STREAM_TO)) and (_rf_src != self.STATUS[_slot]['RX_RFS']):
                    logger.warning('(%s) Packet received with STREAM ID: %s <FROM> SUB: %s REPEATER: %s <TO> TGID %s, SLOT %s collided with existing call', self._system, int_id(_stream_id), int_id(_rf_src), int_id(_radio_id), int_id(_dst_id), _slot)
                    return
                
                # This is a new call stream
                self.STATUS['RX_START'] = pkt_time
                logger.info('(%s) *CALL START* STREAM ID: %s SUB: %s (%s) REPEATER: %s (%s) TGID %s (%s), TS %s', self._system, int_id(_stream_id), sub_alias(_rf_src), int_id(_rf_src), peer_alias(_radio_id), int_id(_radio_id), tg_alias(_dst_id), int_id(_dst_id), _slot)
                
                # If we can, use the LC from the voice header as to keep all options intact
                if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD:
                    decoded = dec_dmr.voice_head_term(dmrpkt)
                    self.STATUS[_slot]['RX_LC'] = decoded['LC']
                
                # If we don't have a voice header then don't wait to decode it from the Embedded LC
                # just make a new one from the HBP header. This is good enough, and it saves lots of time
                else:
                    self.STATUS[_slot]['RX_LC'] = const.LC_OPT + _dst_id + _rf_src


            for rule in RULES[self._system]['GROUP_VOICE']:
                _target = rule['DST_NET']
                _target_status = systems[_target].STATUS
                
                if (rule['SRC_GROUP'] == _dst_id and rule['SRC_TS'] == _slot and rule['ACTIVE'] == True):
                    
                    # BEGIN CONTENTION HANDLING
                    #
                    # The rules for each of the 4 "ifs" below are listed here for readability. The Frame To Send is:
                    #   From a different group than last RX from this HBSystem, but it has been less than Group Hangtime
                    #   From a different group than last TX to this HBSystem, but it has been less than Group Hangtime
                    #   From the same group as the last RX from this HBSystem, but from a different subscriber, and it has been less than stream timeout
                    #   From the same group as the last TX to this HBSystem, but from a different subscriber, and it has been less than stream timeout
                    # The "continue" at the end of each means the next iteration of the for loop that tests for matching rules
                    #
                    if ((rule['DST_GROUP'] != _target_status[rule['DST_TS']]['RX_TGID']) and ((pkt_time - _target_status[rule['DST_TS']]['RX_TIME']) < RULES[_target]['GROUP_HANGTIME'])):
                        if True: #if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD:
                            logger.info('(%s) Call not routed to TGID%s, target active or in group hangtime: HBSystem %s, %s, TGID%s', self._system, int_id(_target_status[rule['DST_TS']]['TX_TGID']), _target, _slot, int_id(rule['DST_GROUP']))
                        continue    
                    if ((rule['DST_GROUP'] != _target_status[rule['DST_TS']]['TX_TGID']) and ((pkt_time - _target_status[rule['DST_TS']]['TX_TIME']) < RULES[_target]['GROUP_HANGTIME'])):
                        if True: #if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD:
                            logger.info('(%s) Call not routed to TGID%s, target in group hangtime: HBSystem %s, %s, TGID%s', self._system, int_id(_target_status[rule['DST_TS']]['TX_TGID']), _target, _slot, int_id(rule['DST_GROUP']))
                        continue
                    if (rule['DST_GROUP'] == _target_status[rule['DST_TS']]['RX_TGID']) and ((pkt_time - _target_status[rule['DST_TS']]['RX_TIME']) < const.STREAM_TO):
                        if True: #if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD:
                            print(repr(rule['DST_GROUP']), repr(_target_status[rule['DST_TS']]['RX_TGID']), pkt_time, _target_status[rule['DST_TS']]['RX_TIME'], const.STREAM_TO)
                            logger.info('(%s) Call not routed, matching call already active on target: HBSystem %s, %s, TGID%s', self._system, _target, _slot, int_id(rule['DST_GROUP']))
                        continue
                    if (rule['DST_GROUP'] == _target_status[rule['DST_TS']]['TX_TGID']) and (_rf_src != _target_status[rule['DST_TS']]['TX_RFS']) and ((pkt_time - _target_status[rule['DST_TS']]['TX_TIME']) < const.STREAM_TO):
                        if True: #if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD:
                            logger.info('(%s) Call not routed, call route in progress from %s, target: HBSystem %s, %s, TGID%s', self._system, _target_status[rule['DST_TS']]['TX_RFS'], _target, _slot, int_id(rule['DST_GROUP']))
                        continue

                    # Set values for the contention handler to test next time there is a frame to forward
                    _target_status[rule['DST_TS']]['TX_TIME'] = pkt_time
                    
                    if _stream_id != self.STATUS[_slot]['RX_STREAM_ID']:
                        # Record the DST TGID and Stream ID
                        _target_status[rule['DST_TS']]['TX_TGID'] = rule['DST_GROUP']
                        _target_status[rule['DST_TS']]['TX_STREAM_ID'] = _stream_id
                        _target_status[rule['DST_TS']]['TX_RFS'] = _rf_src
                        # Generate LCs (full and EMB) for the TX stream
                        # if _dst_id != rule['DST_GROUP']:
                        dst_lc = self.STATUS[_slot]['RX_LC'][0:3] + rule['DST_GROUP'] + _rf_src
                        _target_status[rule['DST_TS']]['TX_H_LC'] = bptc.encode_header_lc(dst_lc)
                        _target_status[rule['DST_TS']]['TX_T_LC'] = bptc.encode_terminator_lc(dst_lc)
                        _target_status[rule['DST_TS']]['TX_EMB_LC'] = bptc.encode_emblc(dst_lc)
                        logger.debug('(%s) Packet DST TGID (%s) does not match SRC TGID(%s) - Generating FULL and EMB LCs', self._system, int_id(rule['DST_GROUP']), int_id(_dst_id))
                    
                    # Handle any necessary re-writes for the destination
                    if rule['SRC_TS'] != rule['DST_TS']:
                        _tmp_bits = _bits ^ 1 << 7
                    else:
                        _tmp_bits = _bits
                    
                    # Assemble transmit HBP packet header
                    _tmp_data = _data[:8] + rule['DST_GROUP'] + _data[11:15] + chr(_tmp_bits) + _data[16:20]
                    
                    # MUST TEST FOR NEW STREAM AND IF SO, RE-WRITE THE LC FOR THE TARGET
                    # MUST RE-WRITE DESTINATION TGID IF DIFFERENT
                    # if _dst_id != rule['DST_GROUP']:
                    dmrbits = bitarray(endian='big')
                    dmrbits.frombytes(dmrpkt)
                    # Create a voice header packet (FULL LC)
                    if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD:
                        dmrbits = _target_status[rule['DST_TS']]['TX_H_LC'][0:98] + dmrbits[98:166] + _target_status[rule['DST_TS']]['TX_H_LC'][98:197]
                    # Create a voice terminator packet (FULL LC)
                    elif _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VTERM:
                        dmrbits = _target_status[rule['DST_TS']]['TX_T_LC'][0:98] + dmrbits[98:166] + _target_status[rule['DST_TS']]['TX_T_LC'][98:197]
                    # Create a Burst B-E packet (Embedded LC)
                    elif _dtype_vseq in [1,2,3,4]:
                        dmrbits = dmrbits[0:116] + _target_status[rule['DST_TS']]['TX_EMB_LC'][_dtype_vseq] + dmrbits[148:264]
                    dmrpkt = dmrbits.tobytes()
                    _tmp_data = _tmp_data + dmrpkt + _data[53:55]
                    
                    # Transmit the packet to the destination system
                    systems[_target].send_system(_tmp_data)
                    logger.debug('(%s) Packet routed by rule: %s to %s system: %s', self._system, rule['NAME'], CONFIG['SYSTEMS'][_target]['MODE'], _target)
            
            
            
            # Final actions - Is this a voice terminator?
            if (_frame_type == const.HBPF_DATA_SYNC) and (_dtype_vseq == const.HBPF_SLT_VTERM) and (self.STATUS[_slot]['RX_TYPE'] != const.HBPF_SLT_VTERM):
                call_duration = pkt_time - self.STATUS['RX_START']
                logger.info('(%s) *CALL END*   STREAM ID: %s SUB: %s (%s) REPEATER: %s (%s) TGID %s (%s), TS %s, Duration: %s', self._system, int_id(_stream_id), sub_alias(_rf_src), int_id(_rf_src), peer_alias(_radio_id), int_id(_radio_id), tg_alias(_dst_id), int_id(_dst_id), _slot, call_duration)
                
                #
                # Begin in-band signalling for call end. This has nothign to do with routing traffic directly.
                #
                
                # Iterate the rules dictionary
                for rule in RULES[self._system]['GROUP_VOICE']:
                    _target = rule['DST_NET']
            
                    # TGID matches a rule source, reset its timer
                    if _slot == rule['SRC_TS'] and _dst_id == rule['SRC_GROUP'] and ((rule['TO_TYPE'] == 'ON' and (rule['ACTIVE'] == True)) or (rule['TO_TYPE'] == 'OFF' and rule['ACTIVE'] == False)):
                        rule['TIMER'] = pkt_time + rule['TIMEOUT']
                        logger.info('(%s) Source group transmission match for rule \"%s\". Reset timeout to %s', self._system, rule['NAME'], rule['TIMER'])
                
                        # Scan for reciprocal rules and reset their timers as well.
                        for target_rule in RULES[_target]['GROUP_VOICE']:
                            if target_rule['NAME'] == rule['NAME']:
                                target_rule['TIMER'] = pkt_time + target_rule['TIMEOUT']
                                logger.info('(%s) Reciprocal group transmission match for rule \"%s\" on IPSC \"%s\". Reset timeout to %s', self._system, target_rule['NAME'], _target, rule['TIMER'])
            
                    # TGID matches an ACTIVATION trigger
                    if _dst_id in rule['ON']:
                        # Set the matching rule as ACTIVE
                        rule['ACTIVE'] = True
                        rule['TIMER'] = pkt_time + rule['TIMEOUT']
                        logger.info('(%s) Primary routing Rule \"%s\" changed to state: %s', self._system, rule['NAME'], rule['ACTIVE'])
                
                        # Set reciprocal rules for other IPSCs as ACTIVE
                        for target_rule in RULES[_target]['GROUP_VOICE']:
                            if target_rule['NAME'] == rule['NAME']:
                                target_rule['ACTIVE'] = True
                                target_rule['TIMER'] = pkt_time + target_rule['TIMEOUT']
                                logger.info('(%s) Reciprocal routing Rule \"%s\" in IPSC \"%s\" changed to state: %s', self._system, target_rule['NAME'], _target, rule['ACTIVE'])
                        
                    # TGID matches an DE-ACTIVATION trigger
                    if _dst_id in rule['OFF']:
                        # Set the matching rule as ACTIVE
                        rule['ACTIVE'] = False
                        logger.info('(%s) Routing Rule \"%s\" changed to state: %s', self._system, rule['NAME'], rule['ACTIVE'])
                
                        # Set reciprocal rules for other IPSCs as ACTIVE
                        _target = rule['DST_NET']
                        for target_rule in RULES[_target]['GROUP_VOICE']:
                            if target_rule['NAME'] == rule['NAME']:
                                target_rule['ACTIVE'] = False
                                logger.info('(%s) Reciprocal routing Rule \"%s\" in IPSC \"%s\" changed to state: %s', self._system, target_rule['NAME'], _target, rule['ACTIVE'])
            #                    
            # END IN-BAND SIGNALLING
            #
                
                
            # Mark status variables for use later
            self.STATUS[_slot]['RX_RFS']       = _rf_src
            self.STATUS[_slot]['RX_TYPE']      = _dtype_vseq
            self.STATUS[_slot]['RX_TGID']      = _dst_id
            self.STATUS[_slot]['RX_TIME']      = pkt_time
            self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id
                

#************************************************
#      MAIN PROGRAM LOOP STARTS HERE
#************************************************

if __name__ == '__main__':
    logger.info('HBlink \'hb_router.py\' (c) 2016 N0MJS & the K0USY Group - SYSTEM STARTING...')
    
    # HBlink instance creation
    # HBlink instance creation
    for system in CONFIG['SYSTEMS']:
        if CONFIG['SYSTEMS'][system]['ENABLED']:
            systems[system] = routerSYSTEM(system)
            reactor.listenUDP(CONFIG['SYSTEMS'][system]['PORT'], systems[system], interface=CONFIG['SYSTEMS'][system]['IP'])
            logger.debug('%s instance created: %s, %s', CONFIG['SYSTEMS'][system]['MODE'], system, systems[system])
            
    # Initialize the rule timer -- this if for user activated stuff
    rule_timer = task.LoopingCall(rule_timer_loop)
    rule_timer.start(60)

    reactor.run()