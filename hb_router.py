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

# Debugging functions
from pprint import pprint

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet import task

# Things we import from the main hblink module
from hblink import CONFIG, HBMASTER, HBCLIENT, logger, masters, clients, hex_str_3, int_id

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
for _system in RULES_FILE['MASTERS']:
    for _rule in RULES_FILE['MASTERS'][_system]['GROUP_VOICE']:
        _rule['SRC_GROUP'] = hex_str_3(_rule['SRC_GROUP'])
        _rule['DST_GROUP'] = hex_str_3(_rule['DST_GROUP'])
        _rule['SRC_TS']    = _rule['SRC_TS']
        _rule['DST_TS']    = _rule['DST_TS']
        for i, e in enumerate(_rule['ON']):
            _rule['ON'][i] = hex_str_3(_rule['ON'][i])
        for i, e in enumerate(_rule['OFF']):
            _rule['OFF'][i] = hex_str_3(_rule['OFF'][i])
    if _system not in CONFIG['MASTERS']:
        sys.exit('ERROR: Routing rules found for MASTER system not configured in main configuration')
for _system in CONFIG['MASTERS']:
    if _system not in RULES_FILE['MASTERS']:
        sys.exit('ERROR: Routing rules not found for all MASTER systems configured')
        
for _system in RULES_FILE['CLIENTS']:
    for _rule in RULES_FILE['CLIENTS'][_system]['GROUP_VOICE']:
        _rule['SRC_GROUP'] = hex_str_3(_rule['SRC_GROUP'])
        _rule['DST_GROUP'] = hex_str_3(_rule['DST_GROUP'])
        _rule['SRC_TS']    = _rule['SRC_TS']
        _rule['DST_TS']    = _rule['DST_TS']
        for i, e in enumerate(_rule['ON']):
            _rule['ON'][i] = hex_str_3(_rule['ON'][i])
        for i, e in enumerate(_rule['OFF']):
            _rule['OFF'][i] = hex_str_3(_rule['OFF'][i])
    if _system not in CONFIG['CLIENTS']:
        sys.exit('ERROR: Routing rules found for CLIENT system not configured in main configuration')
for _system in CONFIG['CLIENTS']:
    if _system not in RULES_FILE['CLIENTS']:
        sys.exit('ERROR: Routing rules not found for all CLIENT systems configured')

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
        
        def dmrd_received(self, _radio_id, _rf_src, _dst_id, _seq, _data):
            for rule in RULES['MASTERS'][self._master]['GROUP_VOICE']:
                _target = rule['DST_NET']
                if _target in RULES['MASTERS']:
                    _tmp_data = _data
                    masters[_target].send_clients(_client, _tmp_data)
                    logger.debug('(%s) Packet routed to master instance: %s', self._master, _target)
                    
                elif _target in RULES['CLIENTS']:
                    _tmp_data = _data
                    _tmp_data = _tmp_data.replace(_radio_id, CONFIG['CLIENTS'][_target]['RADIO_ID'])
                    clients[_target].send_packet(_tmp_data)
                    logger.debug('(%s) Packet routed to client instance: %s', self._master, _target)
                    
                else:
                    logger.debug('(%s) Packet router found no target for packet. Destination was: %s on target network %s', self._master, _dst_id, _target)
                    continue
                

class routerCLIENT(HBCLIENT):
        
        def dmrd_received(self, _radio_id, _rf_src, _dst_id, _seq, _data):
            for rule in RULES['CLIENTS'][self._client]['GROUP_VOICE']:
                _target = rule['DST_NET']
                if _target in RULES['MASTERS']:
                    _tmp_data = _data
                    masters[_target].send_packet(_client, _tmp_data)
                    logger.debug('(%s) Packet routed to master instance: %s', self._client, _target)
                    
                elif _target in RULES['CLIENTS']:
                    _tmp_data = _data
                    _tmp_data = _tmp_data.replace(_radio_id, CONFIG['CLIENTS'][_target]['RADIO_ID'])
                    clients[_target].send_packet(_tmp_data)
                    logger.debug('(%s) Packet routed to client instance: %s', self._client, _target)
                    
                else:
                    logger.debug('(%s) Packet router found no target for packet. Destination was: %s on target network %s', self._client, _dst_id, _target)
                    continue

#************************************************
#      MAIN PROGRAM LOOP STARTS HERE
#************************************************

if __name__ == '__main__':
    logger.info('HBlink \'hb_router.py\' (c) 2016 N0MJS & the K0USY Group - SYSTEM STARTING...')
    
    # HBlink Master
    for master in CONFIG['MASTERS']:
        if CONFIG['MASTERS'][master]['ENABLED']:
            masters[master] = routerMASTER(master)
            reactor.listenUDP(CONFIG['MASTERS'][master]['PORT'], masters[master], interface=CONFIG['MASTERS'][master]['IP'])
            logger.debug('MASTER instance created: %s, %s', master, masters[master])

    for client in CONFIG['CLIENTS']:
        if CONFIG['CLIENTS'][client]['ENABLED']:
            clients[client] = routerCLIENT(client)
            reactor.listenUDP(CONFIG['CLIENTS'][client]['PORT'], clients[client], interface=CONFIG['CLIENTS'][client]['IP'])
            logger.debug('CLIENT instance created: %s, %s', client, clients[client])

    reactor.run()