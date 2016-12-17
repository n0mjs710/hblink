#!/usr/bin/env python
#
###############################################################################
#   Copyright (C) 2016  Cortney T. Buffington, N0MJS <n0mjs@me.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
###############################################################################

from __future__ import print_function

# Python modules we need
import sys
from bitarray import bitarray
from time import time
from importlib import import_module

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet import task

# Things we import from the main hblink module
from hblink import HBSYSTEM, systems, hblink_handler
from dmr_utils.utils import hex_str_3, int_id, get_alias
from dmr_utils import decode, bptc, const
import hb_config
import hb_log
import hb_const

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Colin Durbridge, G4EML, Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'GNU GPLv3'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'
__status__     = 'pre-alpha'

# Module gobal varaibles

# Import Bridging rules
# Note: A stanza *must* exist for any MASTER or CLIENT configured in the main
# configuration file and listed as "active". It can be empty, 
# but it has to exist.
def make_bridges(_hb_confbridge_bridges):
    try:
        bridge_file = import_module(_hb_confbridge_bridges)
        logger.info('Routing bridges file found and bridges imported')
    except ImportError:
        sys.exit('Routing bridges file not found or invalid')
    
    # Convert integer GROUP ID numbers from the config into hex strings
    # we need to send in the actual data packets.
    for _bridge in bridge_file.BRIDGES:
        for _system in bridge_file.BRIDGES[_bridge]:
            if _system['SYSTEM'] not in CONFIG['SYSTEMS']:
                sys.exit('ERROR: Conference bridges found for system not configured main configuration')
                
            _system['TGID']       = hex_str_3(_system['TGID'])
            for i, e in enumerate(_system['ON']):
                _system['ON'][i]  = hex_str_3(_system['ON'][i])
            for i, e in enumerate(_system['OFF']):
                _system['OFF'][i] = hex_str_3(_system['OFF'][i])
            _system['TIMEOUT']    = _system['TIMEOUT']*60
            _system['TIMER']      = time() + _system['TIMEOUT']

    return bridge_file.BRIDGES


# Import subscriber ACL
# ACL may be a single list of subscriber IDs
# Global action is to allow or deny them. Multiple lists with different actions and ranges
# are not yet implemented.
def build_acl(_sub_acl):
    try:
        acl_file = import_module(_sub_acl)
        for i, e in enumerate(acl_file.ACL):
            acl_file.ACL[i] = hex_str_3(acl_file.ACL[i])
        logger.info('ACL file found and ACL entries imported')
    except ImportError:
        logger.info('ACL file not found or invalid - all subscriber IDs are valid')
        ACL_ACTION = 'NONE'

    # Depending on which type of ACL is used (PERMIT, DENY... or there isn't one)
    # define a differnet function to be used to check the ACL
    global allow_sub
    if acl_file.ACL_ACTION == 'PERMIT':
        def allow_sub(_sub):
            if _sub in ACL:
                return True
            else:
                return False
    elif acl_file.ACL_ACTION == 'DENY':
        def allow_sub(_sub):
            if _sub not in ACL:
                return True
            else:
                return False
    else:
        def allow_sub(_sub):
            return True
    
    return acl_file.ACL


# Run this every minute for rule timer updates
def rule_timer_loop():
    logger.info('(ALL HBSYSTEMS) Rule timer loop started')
    _now = time()

    for _bridge in BRIDGES:
        for _system in BRIDGES[_bridge]:
            if _system['TO_TYPE'] == 'ON':
                if _system['ACTIVE'] == True:
                    if _system['TIMER'] < _now:
                        _system['ACTIVE'] = False
                        logger.info('Conference Bridge TIMEOUT: DEACTIVATE System: %s, Bridge: %s, TS: %s, TGID: %s', _system['SYSTEM'], _bridge, _system['TS'], int_id(_system['TGID']))
                    else:
                        timeout_in = _system['TIMER'] - _now
                        logger.info('Conference Bridge ACTIVE (ON timer running): System: %s Bridge: %s, TS: %s, TGID: %s, Timeout in: %ss,', _system['SYSTEM'], _bridge, _system['TS'], int_id(_system['TGID']),  timeout_in)
                elif _system['ACTIVE'] == False:
                    logger.debug('Conference Bridge INACTIVE (no change): System: %s Bridge: %s, TS: %s, TGID: %s', _system['SYSTEM'], _bridge, _system['TS'], int_id(_system['TGID']))
            elif _system['TO_TYPE'] == 'OFF':
                if _system['ACTIVE'] == False:
                    if _system['TIMER'] < _now:
                        _system['ACTIVE'] = True
                        logger.info('Conference Bridge TIMEOUT: ACTIVATE System: %s, Bridge: %s, TS: %s, TGID: %s', _system['SYSTEM'], _bridge, _system['TS'], int_id(_system['TGID']))
                    else:
                        timeout_in = _system['TIMER'] - _now
                        logger.info('Conference Bridge INACTIVE (OFF timer running): System: %s Bridge: %s, TS: %s, TGID: %s, Timeout in: %ss,', _system['SYSTEM'], _bridge, _system['TS'], int_id(_system['TGID']),  timeout_in)
                elif _system['ACTIVE'] == True:
                    logger.debug('Conference Bridge ACTIVE (no change): System: %s Bridge: %s, TS: %s, TGID: %s', _system['SYSTEM'], _bridge, _system['TS'], int_id(_system['TGID']))
            else:
                logger.debug('Conference Bridge NO ACTION: System: %s, Bridge: %s, TS: %s, TGID: %s', _system['SYSTEM'], _bridge, _system['TS'], int_id(_system['TGID']))


class routerSYSTEM(HBSYSTEM):
    
    def __init__(self, _name, _config, _logger):
        HBSYSTEM.__init__(self, _name, _config, _logger)
        
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
                'RX_TYPE':      hb_const.HBPF_SLT_VTERM,
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
                'RX_TYPE':      hb_const.HBPF_SLT_VTERM,
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
            
            # Check for ACL match, and return if the subscriber is not allowed
            if allow_sub(_rf_src) == False:
                self._logger.warning('(%s) Group Voice Packet ***REJECTED BY ACL*** From: %s, HBP Peer %s, Destination TGID %s', self._system, int_id(_rf_src), int_id(_radio_id), int_id(_dst_id))
                return
            
            # Is this a new call stream?   
            if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']):
                if (self.STATUS[_slot]['RX_TYPE'] != hb_const.HBPF_SLT_VTERM) and (pkt_time < (self.STATUS[_slot]['RX_TIME'] + hb_const.STREAM_TO)) and (_rf_src != self.STATUS[_slot]['RX_RFS']):
                    self._logger.warning('(%s) Packet received with STREAM ID: %s <FROM> SUB: %s REPEATER: %s <TO> TGID %s, SLOT %s collided with existing call', self._system, int_id(_stream_id), int_id(_rf_src), int_id(_radio_id), int_id(_dst_id), _slot)
                    return
                
                # This is a new call stream
                self.STATUS['RX_START'] = pkt_time
                self._logger.info('(%s) *CALL START* STREAM ID: %s SUB: %s (%s) REPEATER: %s (%s) TGID %s (%s), TS %s', \
                        self._system, int_id(_stream_id), get_alias(_rf_src, subscriber_ids), int_id(_rf_src), get_alias(_radio_id, peer_ids), int_id(_radio_id), get_alias(_dst_id, talkgroup_ids), int_id(_dst_id), _slot)
                
                # If we can, use the LC from the voice header as to keep all options intact
                if _frame_type == hb_const.HBPF_DATA_SYNC and _dtype_vseq == hb_const.HBPF_SLT_VHEAD:
                    decoded = decode.voice_head_term(dmrpkt)
                    self.STATUS[_slot]['RX_LC'] = decoded['LC']
                
                # If we don't have a voice header then don't wait to decode it from the Embedded LC
                # just make a new one from the HBP header. This is good enough, and it saves lots of time
                else:
                    self.STATUS[_slot]['RX_LC'] = const.LC_OPT + _dst_id + _rf_src


            for _bridge in BRIDGES:
                for _system in BRIDGES[_bridge]:
 
                    if (_system['SYSTEM'] == self._system and _system['TGID'] == _dst_id and _system['TS'] == _slot and _system['ACTIVE'] == True):
                        
                        for _target in BRIDGES[_bridge]:
                            if _target['SYSTEM'] != self._system:                                
                                _target_status = systems[_target['SYSTEM']].STATUS
                                
                                # BEGIN CONTENTION HANDLING
                                #
                                # The rules for each of the 4 "ifs" below are listed here for readability. The Frame To Send is:
                                #   From a different group than last RX from this HBSystem, but it has been less than Group Hangtime
                                #   From a different group than last TX to this HBSystem, but it has been less than Group Hangtime
                                #   From the same group as the last RX from this HBSystem, but from a different subscriber, and it has been less than stream timeout
                                #   From the same group as the last TX to this HBSystem, but from a different subscriber, and it has been less than stream timeout
                                # The "continue" at the end of each means the next iteration of the for loop that tests for matching rules
                                #
                                if ((_target['TGID'] != _target_status[_target['TS']]['RX_TGID']) and ((pkt_time - _target_status[_target['TS']]['RX_TIME']) < self._config['GROUP_HANGTIME'])):
                                    if _frame_type == hb_const.HBPF_DATA_SYNC and _dtype_vseq == hb_const.HBPF_SLT_VHEAD and self.STATUS[_slot]['RX_STREAM_ID'] != _seq:
                                        self._logger.info('(%s) Call not routed to TGID %s, target active or in group hangtime: HBSystem: %s, TS: %s, TGID: %s', self._system, int_id(_target['TGID']), _target['SYSTEM'], _target['TS'], int_id(_target_status[_target['TS']]['RX_TGID']))
                                    continue
                                if ((_target['TGID'] != _target_status[_target['TS']]['TX_TGID']) and ((pkt_time - _target_status[_target['TS']]['TX_TIME']) < self._config['GROUP_HANGTIME'])):
                                    if _frame_type == hb_const.HBPF_DATA_SYNC and _dtype_vseq == hb_const.HBPF_SLT_VHEAD and self.STATUS[_slot]['RX_STREAM_ID'] != _seq:
                                        self._logger.info('(%s) Call not routed to TGID%s, target in group hangtime: HBSystem: %s, TS: %s, TGID: %s', self._system, int_id(_target['TGID']), _target['SYSTEM'], _target['TS'], int_id(_target_status[_target['TS']]['TX_TGID']))
                                    continue
                                if (_target['TGID'] == _target_status[_target['TS']]['RX_TGID']) and ((pkt_time - _target_status[_target['TS']]['RX_TIME']) < hb_const.STREAM_TO):
                                    if _frame_type == hb_const.HBPF_DATA_SYNC and _dtype_vseq == hb_const.HBPF_SLT_VHEAD and self.STATUS[_slot]['RX_STREAM_ID'] != _seq:
                                        self._logger.info('(%s) Call not routed to TGID%s, matching call already active on target: HBSystem: %s, TS: %s, TGID: %s', self._system, int_id(_target['TGID']), _target['SYSTEM'], _target['TS'], int_id(_target_status[_target['TS']]['RX_TGID']))
                                    continue
                                if (_target['TGID'] == _target_status[_target['TS']]['TX_TGID']) and (_rf_src != _target_status[_target['TS']]['TX_RFS']) and ((pkt_time - _target_status[_target['TS']]['TX_TIME']) < hb_const.STREAM_TO):
                                    if _frame_type == hb_const.HBPF_DATA_SYNC and _dtype_vseq == hb_const.HBPF_SLT_VHEAD and self.STATUS[_slot]['RX_STREAM_ID'] != _seq:
                                        self._logger.info('(%s) Call not routed for subscriber %s, call route in progress on target: HBSystem: %s, TS: %s, TGID: %s, SUB: %s', self._system, int_id(_rf_src), _target['SYSTEM'], _target['TS'], int_id(_target_status[_target['TS']]['TX_TGID']), _target_status[_target['TS']]['TX_RFS'])
                                    continue
                                
                                # Set values for the contention handler to test next time there is a frame to forward
                                _target_status[_target['TS']]['TX_TIME'] = pkt_time
                    
                                if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']) or (_target_status[_target['TS']]['TX_RFS'] != _rf_src) or (_target_status[_target['TS']]['TX_TGID'] != _target['TGID']):       
                                    # Record the DST TGID and Stream ID
                                    _target_status[_target['TS']]['TX_TGID'] = _target['TGID']
                                    _target_status[_target['TS']]['TX_STREAM_ID'] = _stream_id
                                    _target_status[_target['TS']]['TX_RFS'] = _rf_src
                                    # Generate LCs (full and EMB) for the TX stream
                                    dst_lc = self.STATUS[_slot]['RX_LC'][0:3] + _target['TGID'] + _rf_src
                                    _target_status[_target['TS']]['TX_H_LC'] = bptc.encode_header_lc(dst_lc)
                                    _target_status[_target['TS']]['TX_T_LC'] = bptc.encode_terminator_lc(dst_lc)
                                    _target_status[_target['TS']]['TX_EMB_LC'] = bptc.encode_emblc(dst_lc)
                                    self._logger.debug('(%s) Generating TX FULL and EMB LCs for destination: System: %s, TS: %s, TGID: %s', self._system, _target['SYSTEM'], _target['TS'], int_id(_target['TGID']))
                                    self._logger.info('(%s) Conference Bridge: %s, Call Bridged to: System: %s TS: %s, TGID: %s', self._system, _bridge, _target['SYSTEM'], _target['TS'], int_id(_target['TGID']))
                    
                                # Handle any necessary re-writes for the destination
                                if _system['TS'] != _target['TS']:
                                    _tmp_bits = _bits ^ 1 << 7
                                else:
                                    _tmp_bits = _bits
                    
                                # Assemble transmit HBP packet header
                                _tmp_data = _data[:8] + _target['TGID'] + _data[11:15] + chr(_tmp_bits) + _data[16:20]
                    
                                # MUST TEST FOR NEW STREAM AND IF SO, RE-WRITE THE LC FOR THE TARGET
                                # MUST RE-WRITE DESTINATION TGID IF DIFFERENT
                                # if _dst_id != rule['DST_GROUP']:
                                dmrbits = bitarray(endian='big')
                                dmrbits.frombytes(dmrpkt)
                                # Create a voice header packet (FULL LC)
                                if _frame_type == hb_const.HBPF_DATA_SYNC and _dtype_vseq == hb_const.HBPF_SLT_VHEAD:
                                    dmrbits = _target_status[_target['TS']]['TX_H_LC'][0:98] + dmrbits[98:166] + _target_status[_target['TS']]['TX_H_LC'][98:197]
                                # Create a voice terminator packet (FULL LC)
                                elif _frame_type == hb_const.HBPF_DATA_SYNC and _dtype_vseq == hb_const.HBPF_SLT_VTERM:
                                    dmrbits = _target_status[_target['TS']]['TX_T_LC'][0:98] + dmrbits[98:166] + _target_status[_target['TS']]['TX_T_LC'][98:197]
                                # Create a Burst B-E packet (Embedded LC)
                                elif _dtype_vseq in [1,2,3,4]:
                                    dmrbits = dmrbits[0:116] + _target_status[_target['TS']]['TX_EMB_LC'][_dtype_vseq] + dmrbits[148:264]
                                dmrpkt = dmrbits.tobytes()
                                _tmp_data = _tmp_data + dmrpkt + _data[53:55]
                    
                                # Transmit the packet to the destination system
                                systems[_target['SYSTEM']].send_system(_tmp_data)
                                #self._logger.debug('(%s) Packet routed by bridge: %s to system: %s TS: %s, TGID: %s', self._system, _bridge, _target['SYSTEM'], _target['TS'], int_id(_target['TGID']))
            
            
            
            # Final actions - Is this a voice terminator?
            if (_frame_type == hb_const.HBPF_DATA_SYNC) and (_dtype_vseq == hb_const.HBPF_SLT_VTERM) and (self.STATUS[_slot]['RX_TYPE'] != hb_const.HBPF_SLT_VTERM):
                call_duration = pkt_time - self.STATUS['RX_START']
                self._logger.info('(%s) *CALL END*   STREAM ID: %s SUB: %s (%s) REPEATER: %s (%s) TGID %s (%s), TS %s, Duration: %s', \
                        self._system, int_id(_stream_id), get_alias(_rf_src, subscriber_ids), int_id(_rf_src), get_alias(_radio_id, peer_ids), int_id(_radio_id), get_alias(_dst_id, talkgroup_ids), int_id(_dst_id), _slot, call_duration)
                
                #
                # Begin in-band signalling for call end. This has nothign to do with routing traffic directly.
                #
                
                # Iterate the rules dictionary
                
                for _bridge in BRIDGES:
                    for _system in BRIDGES[_bridge]:
                        if _system['SYSTEM'] == self._system:
            
                            # TGID matches a rule source, reset its timer
                            if _slot == _system['TS'] and _dst_id == _system['TGID'] and ((_system['TO_TYPE'] == 'ON' and (_system['ACTIVE'] == True)) or (_system['TO_TYPE'] == 'OFF' and _system['ACTIVE'] == False)):
                                _system['TIMER'] = pkt_time + _system['TIMEOUT']
                                self._logger.info('(%s) Transmission match for Bridge: %s. Reset timeout to %s', self._system, _bridge, _system['TIMER'])
            
                            # TGID matches an ACTIVATION trigger
                            if _dst_id in _system['ON']:
                                # Set the matching rule as ACTIVE
                                _system['ACTIVE'] = True
                                _system['TIMER'] = pkt_time + _system['TIMEOUT']
                                self._logger.info('(%s) Bridge: %s, connection changed to state: %s', self._system, _bridge, _system['ACTIVE'])
                        
                            # TGID matches an DE-ACTIVATION trigger
                            if _dst_id in _system['OFF']:
                                # Set the matching rule as ACTIVE
                                _system['ACTIVE'] = False
                                self._logger.info('(%s) Bridge: %s, connection changed to state: %s', self._system, _bridge, _system['ACTIVE'])

            #                    
            # END IN-BAND SIGNALLING
            #
                
                
            # Mark status variables for use later
            self.STATUS[_slot]['RX_SEQ']       = _seq
            self.STATUS[_slot]['RX_RFS']       = _rf_src
            self.STATUS[_slot]['RX_TYPE']      = _dtype_vseq
            self.STATUS[_slot]['RX_TGID']      = _dst_id
            self.STATUS[_slot]['RX_TIME']      = pkt_time
            self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id
                

#************************************************
#      MAIN PROGRAM LOOP STARTS HERE
#************************************************

if __name__ == '__main__':
    
    import argparse
    import sys
    import os
    import signal
    from dmr_utils.utils import try_download, mk_id_dict
    
    # Change the current directory to the location of the application
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

    # CLI argument parser - handles picking up the config file from the command line, and sending a "help" message
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', action='store', dest='CONFIG_FILE', help='/full/path/to/config.file (usually hblink.cfg)')
    parser.add_argument('-l', '--logging', action='store', dest='LOG_LEVEL', help='Override config file logging level.')
    cli_args = parser.parse_args()

    # Ensure we have a path for the config file, if one wasn't specified, then use the default (top of file)
    if not cli_args.CONFIG_FILE:
        cli_args.CONFIG_FILE = os.path.dirname(os.path.abspath(__file__))+'/hblink.cfg'

    # Call the external routine to build the configuration dictionary
    CONFIG = hb_config.build_config(cli_args.CONFIG_FILE)
    
    # Start the system logger
    if cli_args.LOG_LEVEL:
        CONFIG['LOGGER']['LOG_LEVEL'] = cli_args.LOG_LEVEL
    logger = hb_log.config_logging(CONFIG['LOGGER'])
    logger.debug('Logging system started, anything from here on gets logged')
    
    # Set up the signal handler
    def sig_handler(_signal, _frame):
        logger.info('SHUTDOWN: HBROUTER IS TERMINATING WITH SIGNAL %s', str(_signal))
        hblink_handler(_signal, _frame, logger)
        logger.info('SHUTDOWN: ALL SYSTEM HANDLERS EXECUTED - STOPPING REACTOR')
        reactor.stop()
        
    # Set signal handers so that we can gracefully exit if need be
    for sig in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(sig, sig_handler)
    
    # ID ALIAS CREATION
    # Download
    if CONFIG['ALIASES']['TRY_DOWNLOAD'] == True:
        # Try updating peer aliases file
        result = try_download(CONFIG['ALIASES']['PATH'], CONFIG['ALIASES']['PEER_FILE'], CONFIG['ALIASES']['PEER_URL'], CONFIG['ALIASES']['STALE_TIME'])
        logger.info(result)
        # Try updating subscriber aliases file
        result = try_download(CONFIG['ALIASES']['PATH'], CONFIG['ALIASES']['SUBSCRIBER_FILE'], CONFIG['ALIASES']['SUBSCRIBER_URL'], CONFIG['ALIASES']['STALE_TIME'])
        logger.info(result)
        
    # Make Dictionaries
    peer_ids = mk_id_dict(CONFIG['ALIASES']['PATH'], CONFIG['ALIASES']['PEER_FILE'])
    if peer_ids:
        logger.info('ID ALIAS MAPPER: peer_ids dictionary is available')
        
    subscriber_ids = mk_id_dict(CONFIG['ALIASES']['PATH'], CONFIG['ALIASES']['SUBSCRIBER_FILE'])
    if subscriber_ids:
        logger.info('ID ALIAS MAPPER: subscriber_ids dictionary is available')
    
    talkgroup_ids = mk_id_dict(CONFIG['ALIASES']['PATH'], CONFIG['ALIASES']['TGID_FILE'])
    if talkgroup_ids:
        logger.info('ID ALIAS MAPPER: talkgroup_ids dictionary is available')
    
    # Build the routing rules file
    BRIDGES = make_bridges('hb_confbridge_rules')
    
    # Build the Access Control List
    ACL = build_acl('sub_acl')
    
    # HBlink instance creation
    logger.info('HBlink \'hb_router.py\' (c) 2016 N0MJS & the K0USY Group - SYSTEM STARTING...')
    for system in CONFIG['SYSTEMS']:
        if CONFIG['SYSTEMS'][system]['ENABLED']:
            systems[system] = routerSYSTEM(system, CONFIG, logger)
            reactor.listenUDP(CONFIG['SYSTEMS'][system]['PORT'], systems[system], interface=CONFIG['SYSTEMS'][system]['IP'])
            logger.debug('%s instance created: %s, %s', CONFIG['SYSTEMS'][system]['MODE'], system, systems[system])
            
    # Initialize the rule timer -- this if for user activated stuff
    rule_timer = task.LoopingCall(rule_timer_loop)
    rule_timer.start(60)

    reactor.run()