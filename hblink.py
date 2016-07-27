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
            this_master.send_packet(client, 'MSTCL'+client)
            print(CONFIG['MASTERS'][master]['CLIENTS'][client]['RADIO_ID'])
            logger.info('(%s) Sending De-Registration to Client: %s', master, CONFIG['MASTERS'][master]['CLIENTS'][client]['RADIO_ID'])
    
    reactor.stop()

# Set signal handers so that we can gracefully exit if need be
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]:
    signal.signal(sig, handler)


#************************************************
#     UTILITY FUNCTIONS
#************************************************

# Create a 4 byte hex string from an integer
def hex_str_4(_int_id):
    try:
        return hex(_int_id)[2:].rjust(8,'0').decode('hex')
    except TypeError:
        logger.error('hex_str_4: invalid integer length')
        
#************************************************
#     HB MASTER CLASS
#************************************************

class HBMASTER(DatagramProtocol):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            # Define a few shortcuts to make the rest of the class more readable
            self._master = args[0]
            self._config = CONFIG['MASTERS'][self._master]
            self._clients = CONFIG['MASTERS'][self._master]['CLIENTS']
        else:
            # If we didn't get called correctly, log it and quit.
            logger.error('(%s) HBMASTER was not called with an argument. Terminating', self._master)
            sys.exit()
        
    def startProtocol(self):
        # Set up periodic loop for tracking pings from clients. Run every 'PING_TIME' seconds
        self._master_maintenance = task.LoopingCall(self.master_maintenance_loop)
        self._master_maintenance_loop = self._master_maintenance.start(CONFIG['GLOBAL']['PING_TIME'])
    
    def master_maintenance_loop(self):
        logger.debug('(%s) Master maintenance loop started', self._master)
        for client in self._clients.keys():
            _this_client = self._clients[client]
            # Check to see if any of the clients have been quiet (no ping) longer than allowed
            if _this_client['LAST_PING']+CONFIG['GLOBAL']['PING_TIME']*CONFIG['GLOBAL']['MAX_MISSED'] < time():
                logger.info('(%s) Client %s has timed out', self._master, _this_client['RADIO_ID'])
                # Remove any timed out clients from the configuration 
                del CONFIG['MASTERS'][self._master]['CLIENTS'][client]
                
    def send_packet(self, _client, _packet):
        self.transport.write(_packet, (self._clients[_client]['IP'], self._clients[_client]['PORT']))
        # KEEP THE FOLLOWING COMMENTED OUT UNLESS YOU'RE DEBUGGING DEEPLY!!!!
        #logger.debug('(%s) TX Packet to %s on port %s: %s', self._client, self._config['MASTER_IP'], self._config['MASTER_PORT'], h(_packet))
        
    def dmrd_received(self, _radio_id, _data):
        pass    
    
    def datagramReceived(self, _data, (_host, _port)):
            # Extract the command, which is various length, but only 4 significant characters
            _command = _data[:4]
            
            if _command == 'DMRD':    # DMRData -- encapsulated DMR data frame
                _radio_id = _data[4:8]
                if _radio_id in self._clients \
                            and self._clients[_radio_id]['IP'] == _host \
                            and self._clients[_radio_id]['PORT'] == _port:
                    logger.debug('(%s) DMRD Received', self._master)
                    self.dmrd_received(_radio_id, _data)
                else:
                    logger.warning('(%s) DMRD packet recieved from an invalid client')
            
            elif _command == 'RPTL':    # RPTLogin -- a repeater wants to login
                _radio_id = _data[4:8]
                if _radio_id:           # Future check here for valid Radio ID
                    self._clients.update({_radio_id: {      # Build the configuration data strcuture for the client
                        'CONNECTION': 'RPTL-RECEIVED',
                        'PINGS_RECEIVED': 0,
                        'LAST_PING': time(),
                        'IP': _host,
                        'PORT': _port,
                        'SALT': randint(0,0xFFFFFFFF),
                        'RADIO_ID': str(int(h(_radio_id), 16)),
                        'CALLSIGN': '',
                        'RX_FREQ': '',
                        'TX_FREQ': '',
                        'TX_POWER': '',
                        'COLORCODE': '',
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
                    _salt_str = hex_str_4(self._clients[_radio_id]['SALT'])
                    self.send_packet(_radio_id, 'RPTACK'+_salt_str)
                    self._clients[_radio_id]['CONNECTION'] = 'CHALLENGE_SENT'
                    logger.info('(%s) Sent Challenge Response to %s for login: %s', self._master, h(_radio_id), self._clients[_radio_id]['SALT'])
                else:
                    self.transport.write('MSTNAK'+_radio_id, (_host, _port))
                    logger.warning('(%s) Invalid Login from Radio ID: %s', self._master, h(_radio_id))
        
            elif _command == 'RPTK':    # Repeater has answered our login challenge
                _radio_id = _data[4:8]
                if _radio_id in self._clients \
                            and self._clients[_radio_id]['CONNECTION'] == 'CHALLENGE_SENT' \
                            and self._clients[_radio_id]['IP'] == _host \
                            and self._clients[_radio_id]['PORT'] == _port:
                    _this_client = self._clients[_radio_id]
                    _this_client['LAST_PING'] = time()
                    _sent_hash = _data[8:]
                    _salt_str = hex_str_4(_this_client['SALT'])
                    _calc_hash = a(sha256(_salt_str+self._config['PASSPHRASE']).hexdigest())
                    if _sent_hash == _calc_hash:
                        _this_client['CONNECTION'] = 'WAITING_CONFIG'
                        self.send_packet(_radio_id, 'RPTACK'+_radio_id)
                        logger.info('(%s) Client %s has completed the login exchange successfully', self._master, _this_client['RADIO_ID'])
                    else:
                        logger.info('(%s) Client %s has FAILED the login exchange successfully', self._master, _this_client['RADIO_ID'])
                        self.transport.write('MSTNAK'+_radio_id, (_host, _port))
                        del self._clients[_radio_id]
                else:
                    self.transport.write('MSTNAK'+_radio_id, (_host, _port))
                    logger.warning('(%s) Login challenge from Radio ID that has not logged in: %s', self._master, h(_radio_id))
                
            elif _command == 'RPTC':    # Repeater is sending it's configuraiton information
                _radio_id = _data[4:8]
                if _radio_id in self._clients \
                            and self._clients[_radio_id]['CONNECTION'] == 'WAITING_CONFIG' \
                            and self._clients[_radio_id]['IP'] == _host \
                            and self._clients[_radio_id]['PORT'] == _port:
                    _this_client = self._clients[_radio_id]
                    _this_client['CONNECTION'] = 'YES'
                    _this_client['LAST_PING'] = time()
                    _this_client['CALLSIGN'] = _data[8:16]
                    _this_client['RX_FREQ'] = _data[16:25]
                    _this_client['TX_FREQ'] =  _data[25:34]
                    _this_client['TX_POWER'] = _data[34:36]
                    _this_client['COLORCODE'] = _data[36:38]
                    _this_client['LATITUDE'] = _data[38:47]
                    _this_client['LONGITUDE'] = _data[47:57]
                    _this_client['HEIGHT'] = _data[57:60]
                    _this_client['LOCATION'] = _data[60:80]
                    _this_client['DESCRIPTION'] = _data[80:99]
                    _this_client['SLOTS'] = _data[99:100]
                    _this_client['URL'] = _data[100:224]
                    _this_client['SOFTWARE_ID'] = _data[224:264]
                    _this_client['PACKAGE_ID'] = _data[264:304]
    
                    self.send_packet(_radio_id, 'RPTACK'+_radio_id)
                    logger.info('(%s) Client %s has sent repeater configuration', self._master, _this_client['RADIO_ID'])
                else:
                    self.transport.write('MSTNAK'+_radio_id, (_host, _port))
                    logger.warning('(%s) Client info from Radio ID that has not logged in: %s', self._master, h(_radio_id))

            elif _command == 'RPTP':    # RPTPing -- client is pinging us
                    _radio_id = _data[7:11]
                    if _radio_id in self._clients \
                                and self._clients[_radio_id]['CONNECTION'] == "YES" \
                                and self._clients[_radio_id]['IP'] == _host \
                                and self._clients[_radio_id]['PORT'] == _port:
                        self._clients['LAST_PING'] = time()
                        self.send_packet(_radio_id, 'MSTPONG'+_radio_id)
                        logger.info('(%s) Received and answered RPTPING from client %s', self._master, h(_radio_id))
                    else:
                        self.transport.write('MSTNAK'+_radio_id, (_host, _port))
                        logger.warning('(%s) Client info from Radio ID that has not logged in: %s', self._master, h(_radio_id))
                        
            else:
                logger.error('(%s) Unrecognized command from: %s. Packet: %s', self._master, h(_radio_id), h(_data))
            
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
        logger.debug('(%s) Client maintenance loop started', self._client)
        # If we're not connected, zero out the stats and send a login request RPTL
        if self._stats['CONNECTION'] == 'NO':
            self._stats['PINGS_SENT'] = 0
            self._stats['PINGS_ACKD'] = 0
            self._stats['CONNECTION'] = 'RTPL_SENT'
            self.send_packet('RPTL'+self._config['RADIO_ID'])
            logger.info('(%s) Sending login request to master', self._client)
        # If we are connected, sent a ping to the master and increment the counter
        if self._stats['CONNECTION'] == 'YES':
            self.send_packet('RPTPING'+self._config['RADIO_ID'])
            self._stats['PINGS_SENT'] += 1
            logger.info('(%s) RPTPING Sent to Master. Pings Since Connected: %s', self._client, self._stats['PINGS_SENT'])
        
    def send_packet(self, _packet):
        self.transport.write(_packet, (self._config['MASTER_IP'], self._config['MASTER_PORT']))
        # KEEP THE FOLLOWING COMMENTED OUT UNLESS YOU'RE DEBUGGING DEEPLY!!!!
        #logger.debug('(%s) TX Packet to %s on port %s: %s', self._client, self._config['MASTER_IP'], self._config['MASTER_PORT'], h(_packet))
    
    def dmrd_received(self, _radio_id, _data):
        pass
    
    def datagramReceived(self, _data, (_host, _port)):
        # Validate that we receveived this packet from the master - security check!
        if self._config['MASTER_IP'] == _host and self._config['MASTER_PORT'] == _port:
            # Extract the command, which is various length, but only 4 significant characters
            _command = _data[:4] 
            if   _command == 'DMRD':    # DMRData -- encapsulated DMR data frame
                _radio_id = _data[4:8]
                if self._config['RADIO_ID'] == _radio_id: # Check to ensure this packet is meant for us
                    logger.debug('(%s) DMRD Received', self._client)
                    self.dmrd_received(_radio_id, _data)
        
            elif _command == 'MSTN':    # Actually MSTNAK -- a NACK from the master
                if self._config['RADIO_ID'] == _radio_id: # Check to ensure this packet is meant for us
                    print('(%s) MSTNAK Received', self._client)
                    self._stats['CONNECTION'] = 'NO' # Disconnect ourselves and re-register
        
            elif _command == 'RPTA':    # Actually RPTACK -- an ACK from the master
                # Depending on the state, an RPTACK means different things, in each clause, we check and/or set the state
                if self._stats['CONNECTION'] == 'RTPL_SENT': # If we've sent a login request...
                    _login_int32 = _data[6:10]
                    logger.info('(%s) Repeater Login ACK Received with 32bit ID: %s', self._client, h(_login_int32))
                    _pass_hash = sha256(_login_int32+self._config['PASSPHRASE']).hexdigest()
                    _pass_hash = a(_pass_hash)
                    self.send_packet('RPTK'+self._config['RADIO_ID']+_pass_hash)
                    self._stats['CONNECTION'] = 'AUTHENTICATED'
        
                elif self._stats['CONNECTION'] == 'AUTHENTICATED': # If we've sent the login challenge...
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
                
                elif self._stats['CONNECTION'] == 'CONFIG-SENT': # If we've sent out configuration to the master
                    if _data[6:10] == self._config['RADIO_ID']:
                        logger.info('(%s) Repeater Configuration Accepted', self._client)
                        self._stats['CONNECTION'] = 'YES'
                        logger.info('(%s) Connection to Master Completed', self._client)
                    else:
                        self._stats['CONNECTION'] = 'NO'
                        logger.error('(%s) Master ACK Contained wrong ID - Connection Reset', self._client)
                
            elif _command == 'MSTP':    # Actually MSTPONG -- a reply to RPTPING (send by client)
                if _data [7:11] == self._config['RADIO_ID']:
                    self._stats['PINGS_ACKD'] += 1
                    logger.info('(%s) MSTPONG Received. Total Pongs Since Connected: %s', self._client, self._stats['PINGS_ACKD'])
        
            elif _command == 'MSTC':    # Actually MSTCL -- notify us the master is closing down
                if _data[5:9] == self._config['RADIO_ID']:
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
