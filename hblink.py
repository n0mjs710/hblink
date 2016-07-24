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
import signal

# Specifig functions from modules we need
from binascii import b2a_hex as h
from binascii import a2b_hex as a
from socket import gethostbyname
from random import randint
from hashlib import sha256
from time import time

# Debugging functions
from pprint import pprint

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet import task

# Other files we pull from -- this is mostly for readability and segmentation
import hb_log
import hb_config

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2013 - 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Colin Durbridge, G4EML, Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
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

# Shut ourselves down gracefully by disconnecting from the masters and clients.
def handler(_signal, _frame):
    logger.info('*** HBLINK IS TERMINATING WITH SIGNAL %s ***', str(_signal))
    
    for client in clients:
        this_client = clients[client]
        this_client.send_packet('RPTCL'+CONFIG['CLIENTS'][client]['RADIO_ID'])
        logger.info('(%s) De-Registering From the Master', client)
        
    for master in masters:
        this_master = masters[master]
        for client in CONFIG['MASTERS'][master]['CLIENTS']:
            this_master.send_packet(CONFIG['MASTERS'][master][client]['IP'], 'MSTCL'+CONFIG['MASTERS'][master][client]['RADIO_ID'])
    
    reactor.stop()

# Set signal handers so that we can gracefully exit if need be
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]:
    signal.signal(sig, handler)


#************************************************
#     UTILITY FUNCTIONS
#************************************************


#************************************************
#     HB MASTER CLASS
#************************************************

class HBMASTER(DatagramProtocol):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            self._master = args[0]
            self._config = CONFIG['MASTERS'][self._master]
            self._clients = CONFIG['MASTERS'][self._master]['CLIENTS']
        else:
            # If we didn't get called correctly, log it!
            logger.error('(%s) HBMASTER was not called with an argument. Terminating', self._master)
            sys.exit()
        
    def startProtocol(self):
        # Set up periodic loop for tracking pings from clients. Run every 'PING_TIME' seconds
        self._master_maintenance = task.LoopingCall(self.master_maintenance_loop)
        self._master_maintenance_loop = self._master_maintenance.start(CONFIG['GLOBAL']['PING_TIME'])
    
    def master_maintenance_loop(self):
        for client in self._clients:
            logger.info('(%s) SOME MESSAGE ABOUT DE_REG', self._master)
            
    def send_packet(self, _client, _packet):
        self.transport.write(_packet, (self._clients[client]['IP'], self._clients[client]['PORT']))
        # KEEP THE FOLLOWING COMMENTED OUT UNLESS YOU'RE DEBUGGING DEEPLY!!!!
        #logger.debug('(%s) TX Packet to %s on port %s: %s', self._client, self._config['MASTER_IP'], self._config['MASTER_PORT'], h(_packet))
        
    def datagramReceived(self, _data, (_host, _port)):
        
        _command = _data[:4]
        if   _command == 'DMRD':    # DMRData -- encapsulated DMR data frame
            logger.debug('(%s) DMRD Received', self._master)
            
        elif _command == 'RPTL':    # RPTLogin -- a repeater wants to login
            _radio_id = _data[4:8]
            self._clients.update({_radio_id: {
                'CONNECTION': 'RPTL-RECEIVED',
                'PINGS_RECEIVED': 0,
                'LAST_PING': 0,
                'IP': _host,
                'PORT': _port,
                'SALT': randint(0,0xFFFFFFFF),
                'RADIO_ID': str(int(h(_radio_id), 16)),
                'CALLSIGN': '',
                'RX_FREQ': '',
                'TX_FREQ': '',
                'TX_POWER': '',
                'COLOR_CODE': '',
                'LATITUDE': '',
                'LONGITUDE': '',
                'HEIGHT': '',
                'LOCATION': '',
                'DESCRIPTION': '',
                'SLOTS': '',
                'URL': '',
                'SOFTWARE_ID': '',
                'PACKAGE_ID': '',
            }})
            logger.info('(%s) Repeater Logging in with Radio ID: %s', self._master, h(_radio_id))
            pprint(self._clients)
            
#************************************************
#     HB CLIENT CLASS
#************************************************            
    
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
            
    def startProtocol(self):
        # Set up periodic loop for sending pings to the master. Run every 'PING_TIME' seconds
        self._client_maintenance = task.LoopingCall(self.client_maintenance_loop)
        self._client_maintenance_loop = self._client_maintenance.start(CONFIG['GLOBAL']['PING_TIME'])
        
    def client_maintenance_loop(self):
        if self._stats['CONNECTION'] == 'NO':
            self._stats['PINGS_SENT'] = 0
            self._stats['PINGS_ACKD'] = 0
            self._stats['CONNECTION'] = 'RTPL_SENT'
            self.send_packet('RPTL'+self._config['RADIO_ID'])
            logger.info('(%s) Sending login request to master', self._client)
        if self._stats['CONNECTION'] == 'YES':
            self.send_packet('RPTPING'+self._config['RADIO_ID'])
            self._stats['PINGS_SENT'] += 1
            logger.info('(%s) RPTPING Sent to Master. Total Pings Since Connected: %s', self._client, self._stats['PINGS_SENT'])
        
    def send_packet(self, _packet):
        self.transport.write(_packet, (self._config['MASTER_IP'], self._config['MASTER_PORT']))
        # KEEP THE FOLLOWING COMMENTED OUT UNLESS YOU'RE DEBUGGING DEEPLY!!!!
        #logger.debug('(%s) TX Packet to %s on port %s: %s', self._client, self._config['MASTER_IP'], self._config['MASTER_PORT'], h(_packet))
    
    def datagramReceived(self, _data, (_host, _port)):
        
        _command = _data[:4]
        if   _command == 'DMRD':    # DMRData -- encapsulated DMR data frame
            logger.debug('(%s) DMRD Received', self._client)
        
        elif _command == 'MSTN':    # Actually MSTNAK -- a NACK from the master
            print('(%s) MSTNAC Received', self._client)
            self._stats['CONNECTION'] = 'NO'
        
        elif _command == 'RPTA':    # Actually RPTACK -- an ACK from the master
            if self._stats['CONNECTION'] == 'RTPL_SENT':
                _login_int32 = _data[6:10]
                logger.info('(%s) Repeater Login ACK Received with 32bit ID: %s', self._client, h(_login_int32))
                _pass_hash = sha256(_login_int32+self._config['PASSPHRASE']).hexdigest()
                _pass_hash = a(_pass_hash)
                self.send_packet('RPTK'+self._config['RADIO_ID']+_pass_hash)
                self._stats['CONNECTION'] = 'AUTHENTICATED'
            
            elif self._stats['CONNECTION'] == 'AUTHENTICATED':
                if _data[6:10] == self._config['RADIO_ID']:
                    logger.info('(%s) Repeater Authentication Accepted', self._client)
                    _config_packet =  self._config['RADIO_ID']+\
                                      self._config['CALLSIGN']+\
                                      self._config['RX_FREQ']+\
                                      self._config['TX_FREQ']+\
                                      self._config['TX_POWER']+\
                                      self._config['COLORCODE']+\
                                      self._config['LATITUDE']+\
                                      self._config['LONGITUDE']+\
                                      self._config['HEIGHT']+\
                                      self._config['LOCATION']+\
                                      self._config['DESCRIPTION']+\
                                      self._config['SLOTS']+\
                                      self._config['URL']+\
                                      self._config['SOFTWARE_ID']+\
                                      self._config['PACKAGE_ID']
                                      
                    self.send_packet('RPTC'+_config_packet)
                    self._stats['CONNECTION'] = 'CONFIG-SENT'
                    logger.info('(%s) Repeater Configuration Sent', self._client)
                else:
                    self._stats['CONNECTION'] = 'NO'
                    logger.error('(%s) Master ACK Contained wrong ID - Connection Reset', self._client)
                    
            elif self._stats['CONNECTION'] == 'CONFIG-SENT':
                if _data[6:10] == self._config['RADIO_ID']:
                    logger.info('(%s) Repeater Configuration Accepted', self._client)
                    self._stats['CONNECTION'] = 'YES'
                    logger.info('(%s) Connection to Master Completed', self._client)
                else:
                    self._stats['CONNECTION'] = 'NO'
                    logger.error('(%s) Master ACK Contained wrong ID - Connection Reset', self._client)
                
        elif _command == 'MSTP':    # Actually MSTPONG -- a reply to RPTPING (send by client)
            self._stats['PINGS_ACKD'] += 1
            logger.info('(%s) MSTPONG Received. Total Pongs Since Connected: %s', self._client, self._stats['PINGS_ACKD'])
        
        elif _command == 'MSTC':    # Actually MSTCL -- notify us the master is closing down
            self._stats['CONNECTION'] = 'NO'
            logger.info('(%s) MSTCL Recieved', self._client)
        
        else:
            logger.error('(%s) Received an invalid command in packet: %s', self._client, h(_data))
 
        # Keep This Line Commented Unless HEAVILY Debugging!
        #logger.debug('(%s) Received Packet: %s', self._client, h(_data))


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