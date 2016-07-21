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
from socket import gethostbyname
from pprint import pprint

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

# Other files we pull from -- this is mostly for readability and segmentation
import hb_log
import hb_config
import hb_message_types

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
    
class HBCLIENT(DatagramProtocol):
    def __init__(self, *args, **kwargs):
        pass



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