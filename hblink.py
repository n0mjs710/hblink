#!/usr/bin/env python
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from __future__ import print_function

# Python modules we need
import argparse
import sys
import os

# Specifig functions from modules we need
from binascii import b2a_hex as h
from binascii import a2b_hex as a
from socket import gethostbyname
from random import randint
from hashlib import sha256

# Debugging functions
from pprint import pprint

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet import task

# Other files we pull from -- this is mostly for readability and segmentation
import hb_log
import hb_config
from hb_message_types import *

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2013 - 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'
__status__     = 'pre-alpha'


# Change the current directory to the location of the application
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))


# CLI argument parser - handles picking up the config file from the command line, and sending a "help" message
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', action='store', dest='CONFIG_FILE', help='/full/path/to/config.file (usually hblink.cfg)')
parser.add_argument('-l', '--logging', action='store', dest='LOG_LEVEL', help='Override config file logging level.')
cli_args = parser.parse_args()


# Ensure we have a path for the config file, if one wasn't specified, then use the execution directory
if not cli_args.CONFIG_FILE:
    cli_args.CONFIG_FILE = os.path.dirname(os.path.abspath(__file__))+'/hblink.cfg'


# Call the external routine to build the configuration dictionary
CONFIG = hb_config.build_config(cli_args.CONFIG_FILE)


# Call the external routing to start the system logger
if cli_args.LOG_LEVEL:
    CONFIG['LOGGER']['LOG_LEVEL'] = cli_args.LOG_LEVEL
logger = hb_log.config_logging(CONFIG['LOGGER'])
logger.debug('Logging system started, anything from here on gets logged')



#************************************************
#     HERE ARE THE IMPORTANT PARTS
#************************************************

class HBMASTER(DatagramProtocol):
    def __init__(self, *args, **kwargs):
        pass
        
    def startProtocol(self):
        pass
    
    
    
class HBCLIENT(DatagramProtocol):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            self._client = args[0]
            self._config = CONFIG['CLIENTS'][self._client]
            self._stats = self._config['STATS']
        else:
            # If we didn't get called correctly, log it!
            logger.error('(%s) HBCLIENT was not called with an argument. Terminating', self._client)
            sys.exit()
            
    def send_packet(self, _packet):
        print('did this')
        self.transport.write(_packet, (self._config['MASTER_IP'], self._config['MASTER_PORT']))
        # KEEP THE FOLLOWING COMMENTED OUT UNLESS YOU'RE DEBUGGING DEEPLY!!!!
        logger.debug('(%s) TX Packet to %s on port %s: %s', self._client, self._config['MASTER_IP'], self._config['MASTER_PORT'], h(_packet))        
            
    def startProtocol(self):
        # Set up periodic loop for sending pings to the master. Run every minute
        self._peer_maintenance = task.LoopingCall(self.peer_maintenance_loop)
        self._peer_maintenance_loop = self._peer_maintenance.start(10)
        
    def peer_maintenance_loop(self):
        if self._stats['CONNECTED'] == False:
            self.send_packet(RPTL+self._config['RADIO_ID'])
            
        logger.debug('(%s) Sending ping to Master', self._client)
        ###### change timing after connected: self._peer_maintenance_loop = self._peer_maintenance._reschedule(60)
        
    def send_packet(self, _packet):
        self.transport.write(_packet, (self._config['MASTER_IP'], self._config['MASTER_PORT']))
        # KEEP THE FOLLOWING COMMENTED OUT UNLESS YOU'RE DEBUGGING DEEPLY!!!!
        logger.debug('(%s) TX Packet to %s on port %s: %s', self._client, self._config['MASTER_IP'], self._config['MASTER_PORT'], h(_packet))
    
    def datagramReceived(self, _data, (_host, _port)):
        
        _command = _data[:4]
        if   _command == 'DMRD':    # DMRData -- encapsulated DMR data frame
            print('DMRD Received')
        elif _command == 'MSTN':    # Actually MSTNAK -- a NACK from the master
            print('MSTNAC Received')
        elif _command == 'RPTA':    # Actually RPTACK -- an ACK from the master
            _login_int32 = _data[6:10]
            logger.info('(%s) Repeater Login ACK Received with 32bit ID: %s', self._client, h(_login_int32))
            _pass_hash = a(sha256(h(_login_int32).upper()+self._config['PASSPHRASE']).hexdigest())
            self.send_packet('RPTK'+self._config['RADIO_ID']+_pass_hash)
        elif _command == 'RPTP':    # Actually RPTPONG -- a reply to MSTPING (send by client)
            print('RPTPONG Received')
        elif _command == 'MSTC':    # Actually MSTCL -- notify the master this client is closing
            print('MSTCL Recieved')
        else:
            logger.error('(%s) Received an invalid command in packet: %s', self._client, h(_data))
 
    
        print('Received Packet:', h(_data))


#************************************************
#      MAIN PROGRAM LOOP STARTS HERE
#************************************************

if __name__ == '__main__':
    logger.info('HBlink \'HBlink.py\' (c) 2016 N0MJS & the K0USY Group - SYSTEM STARTING...')
    
    # HBlink Master
    masters = {}
    for master in CONFIG['MASTERS']:
        if CONFIG['MASTERS'][master]['ENABLED']:
            masters[master] = HBMASTER(master)
            reactor.listenUDP(CONFIG['MASTERS'][master]['PORT'], masters[master], interface=CONFIG['MASTERS'][master]['IP'])
            logger.debug('MASTER instance created: %s, %s', master, masters[master])
        
    clients = {}
    for client in CONFIG['CLIENTS']:
        if CONFIG['CLIENTS'][client]['ENABLED']:
            clients[client] = HBCLIENT(client)
            reactor.listenUDP(CONFIG['CLIENTS'][client]['PORT'], clients[client], interface=CONFIG['CLIENTS'][client]['IP'])
            logger.debug('CLIENT instance created: %s, %s', client, clients[client])

    reactor.run()