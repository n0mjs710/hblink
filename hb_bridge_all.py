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

'''
This is a very simple call/packet router for Homebrew Repeater Protocol. It
will forward traffic from any system to all other systems configured in the
hblink.py configuration file. It does not check for call contentions or
filter TS/TGID combinations. It should really only be used as a proxy to
hide multiple Homebrew repater protocol systems behind what appears as a single
repeater, hotspot, etc.

As is, this program only works with group voice packets. It could work for all
of them by removing a few things.
'''

from __future__ import print_function

# Python modules we need
import sys
from bitarray import bitarray
from time import time
from importlib import import_module
from types import ModuleType

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import reactor, task

# Things we import from the main hblink module
from hblink import HBSYSTEM, systems, hblink_handler, reportFactory, REPORT_OPCODES, config_reports, build_reg_acl
from dmr_utils.utils import hex_str_3, int_id, get_alias
from dmr_utils import decode, bptc, const
from acl import acl_check, acl_build
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


# Import rules -- at this point, just ACLs
def import_rules(_rules):
    try:
        rules_file = import_module(_rules)
        logger.info('Rules file found and bridges imported')
        return rules_file
    except ImportError:
        logger.info('Rules file not found. Initializing defaults')
        rules_file = ModuleType('rules_file')
        rules_file.ACL = {'SID':{}, 'TGID':{}}
        return rules_file


class bridgeallSYSTEM(HBSYSTEM):
    
    def __init__(self, _name, _config, _logger, _report):
        HBSYSTEM.__init__(self, _name, _config, _logger, _report)
        
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
            
            # Check for GLOBAL Subscriber ID ACL Match
            if acl_check(_rf_src, ACL['SID']['GLOBAL'][_slot]) == False:
                if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']):
                    self._logger.warning('(%s) Group Voice Call ***REJECTED BY INGRESS GLOBAL ACL***    SID: %s SLOT: %s HBP Peer %s', self._system, int_id(_rf_src), _slot, int_id(_radio_id))
                    self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id
                return
            # Check for SYSTEM Subscriber ID ACL Match
            if acl_check(_rf_src, ACL['SID'][self._system][_slot]) == False:
                if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']):
                    self._logger.warning('(%s) Group Voice Call ***REJECTED BY INGRESS SYSTEM ACL***    SID: %s SLOT: %s HBP Peer %s', self._system, int_id(_rf_src), _slot, int_id(_radio_id))
                    self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id
                return
            
            # Check for GLOBAL Talkgroup ID ACL Match    
            if acl_check(_dst_id, ACL['TGID']['GLOBAL'][_slot]) == False:
                if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']):
                    self._logger.warning('(%s) Group Voice Call ***REJECTED BY INGRESS GLOBAL ACL***    TGID: %s SLOT: %s HBP Peer %s', self._system, int_id(_dst_id), _slot, int_id(_radio_id))
                    self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id
                return
            # Check for SYSTEM Talkgroup ID ID ACL Match
            if acl_check(_dst_id, ACL['TGID'][self._system][_slot]) == False:
                if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']):
                    self._logger.warning('(%s) Group Voice Call ***REJECTED BY INGRESS SYSTEM ACL***    TGID: %s SLOT: %s HBP Peer %s', self._system, int_id(_dst_id), _slot, int_id(_radio_id))
                    self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id
                return
            
            # Is this is a new call stream?
            if (_stream_id != self.STATUS[_slot]['RX_STREAM_ID']):
                self.STATUS['RX_START'] = pkt_time
                self._logger.info('(%s) *CALL START* STREAM ID: %s SUB: %s (%s) REPEATER: %s (%s) TGID %s (%s), TS %s', \
                        self._system, int_id(_stream_id), get_alias(_rf_src, subscriber_ids), int_id(_rf_src), get_alias(_radio_id, peer_ids), int_id(_radio_id), get_alias(_dst_id, talkgroup_ids), int_id(_dst_id), _slot)
            
            # Final actions - Is this a voice terminator?
            if (_frame_type == hb_const.HBPF_DATA_SYNC) and (_dtype_vseq == hb_const.HBPF_SLT_VTERM) and (self.STATUS[_slot]['RX_TYPE'] != hb_const.HBPF_SLT_VTERM):
                call_duration = pkt_time - self.STATUS['RX_START']
                self._logger.info('(%s) *CALL END*   STREAM ID: %s SUB: %s (%s) REPEATER: %s (%s) TGID %s (%s), TS %s, Duration: %s', \
                        self._system, int_id(_stream_id), get_alias(_rf_src, subscriber_ids), int_id(_rf_src), get_alias(_radio_id, peer_ids), int_id(_radio_id), get_alias(_dst_id, talkgroup_ids), int_id(_dst_id), _slot, call_duration)
            
            # Mark status variables for use later
            self.STATUS[_slot]['RX_RFS']       = _rf_src
            self.STATUS[_slot]['RX_TYPE']      = _dtype_vseq
            self.STATUS[_slot]['RX_TGID']      = _dst_id
            self.STATUS[_slot]['RX_TIME']      = pkt_time
            self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id
            
            
            for _target in self._CONFIG['SYSTEMS']: 
                    if _target != self._system:
                        
                        _target_status = systems[_target].STATUS
                        _target_system = self._CONFIG['SYSTEMS'][_target]
                        
                        # Check for GLOBAL Subscriber ID ACL Match
                        if acl_check(_rf_src, ACL['SID']['GLOBAL'][_slot]) == False:
                            if (_stream_id != _target_status[_slot]['TX_STREAM_ID']):
                                self._logger.warning('(%s) Group Voice Call ***REJECTED BY EGRESS GLOBAL ACL***    SID: %s SLOT: %s HBP Peer %s', _target, int_id(_rf_src), _slot, int_id(_radio_id))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            return
                        # Check for SYSTEM Subscriber ID ACL Match
                        if acl_check(_rf_src, ACL['SID'][_target][_slot]) == False:
                            if (_stream_id != _target_status[_slot]['TX_STREAM_ID']):
                                self._logger.warning('(%s) Group Voice Call ***REJECTED BY EGRESS SYSTEM ACL***    SID: %s SLOT: %s HBP Peer %s', _target, int_id(_rf_src), _slot, int_id(_radio_id))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            return
            
                        # Check for GLOBAL Talkgroup ID ACL Match    
                        if acl_check(_dst_id, ACL['TGID']['GLOBAL'][_slot]) == False:
                            if (_stream_id != _target_status[_slot]['TX_STREAM_ID']):
                                self._logger.warning('(%s) Group Voice Call ***REJECTED BY EGRESS GLOBAL ACL***    TGID: %s SLOT: %s HBP Peer %s', _target, int_id(_dst_id), _slot, int_id(_radio_id))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            return
                        # Check for SYSTEM Talkgroup ID ID ACL Match
                        if acl_check(_dst_id, ACL['TGID'][_target][_slot]) == False:
                            if (_stream_id != _target_status[_slot]['TX_STREAM_ID']):
                                self._logger.warning('(%s) Group Voice Call ***REJECTED BY EGRESS SYSTEM ACL***    TGID: %s HBP Peer %s', _target, int_id(_dst_id), int_id(_radio_id))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            return
                        
                        systems[_target].send_system(_data)
                        #self._logger.debug('(%s) Packet routed to system: %s', self._system, _target)
            
            
            

                

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
        
    # Build the Access Control List
    REG_ACL = build_reg_acl('reg_acl', logger)
    
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
        
    # Import rules file
    rules_file = import_rules('hb_bridge_all_rules')
        
    # Create ACLs
    ACL = rules_file.ACL
    
    for acl_type in ACL:
        if acl_type != 'SID' and acl_type != 'TGID':
            sys.exit(('TERMINATE: SID or TGID stanzas not in ACL!!! Exiting to save you grief later'))
        
        if 'GLOBAL' not in ACL[acl_type]:
            ACL[acl_type].update({'GLOBAL': {1:'PERMIT:ALL',2:'PERMIT:ALL'}})
            
        for system_acl in ACL[acl_type]:
            if system_acl not in CONFIG['SYSTEMS'] and system_acl != 'GLOBAL':
                sys.exit(('TERMINATE: {} ACL configured for system {} that does not exist!!! Exiting to save you grief later'.format(acl_type, system_acl)))
            for slot in ACL[acl_type][system_acl]:
                ACL[acl_type][system_acl][slot] = acl_build(ACL[acl_type][system_acl][slot])
            
    for system in CONFIG['SYSTEMS']:
        for acl_type in ACL:
            if system not in ACL[acl_type]:
                logger.warning('No %s  ACL for system %s - initializing \'PERMIT:ALL\'', acl_type, system)
                ACL[acl_type].update({system: {1: acl_build('PERMIT:ALL'), 2: acl_build('PERMIT:ALL')}})
    
    # INITIALIZE THE REPORTING LOOP
    report_server = config_reports(CONFIG, logger, reportFactory)
    
    # HBlink instance creation
    logger.info('HBlink \'hb_bridge_all.py\' (c) 2016 N0MJS & the K0USY Group - SYSTEM STARTING...')
    for system in CONFIG['SYSTEMS']:
        if CONFIG['SYSTEMS'][system]['ENABLED']:
            systems[system] = bridgeallSYSTEM(system, CONFIG, logger, report_server)
            reactor.listenUDP(CONFIG['SYSTEMS'][system]['PORT'], systems[system], interface=CONFIG['SYSTEMS'][system]['IP'])
            logger.debug('%s instance created: %s, %s', CONFIG['SYSTEMS'][system]['MODE'], system, systems[system])

    reactor.run()
