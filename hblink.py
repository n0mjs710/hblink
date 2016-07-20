#!/usr/bin/env python
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from __future__ import print_function

import ConfigParser
import argparse
import sys
import os
import logging

from logging.config import dictConfig
from binascii import b2a_hex as h
from socket import gethostbyname 

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2013 - 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'
__status__     = 'pre-alpha'

# Change the current directory to the location of the application
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', action='store', dest='CFG_FILE', help='/full/path/to/config.file (usually hblink.cfg)')

cli_args = parser.parse_args()

#************************************************
#     PARSE THE CONFIG FILE AND BUILD STRUCTURE
#************************************************

CLIENTS = {}
config = ConfigParser.ConfigParser()

if not cli_args.CFG_FILE:
    cli_args.CFG_FILE = os.path.dirname(os.path.abspath(__file__))+'/hblink.cfg'
try:
    if not config.read(cli_args.CFG_FILE):
        sys.exit('Configuration file \''+cli_args.CFG_FILE+'\' is not a valid configuration file! Exiting...')        
except:    
    sys.exit('Configuration file \''+cli_args.CFG_FILE+'\' is not a valid configuration file! Exiting...')

try:
    for section in config.sections():
        if section == 'GLOBAL':
            # Process GLOBAL items in the configuration
            PATH = config.get(section, 'PATH')
        
        elif section == 'LOGGER':
            # Process LOGGER items in the configuration
            LOGGER = {
                'LOG_FILE': config.get(section, 'LOG_FILE'),
                'LOG_HANDLERS': config.get(section, 'LOG_HANDLERS'),
                'LOG_LEVEL': config.get(section, 'LOG_LEVEL'),
                'LOG_NAME': config.get(section, 'LOG_NAME')
            }
            
        elif section == 'MASTER':
            # HomeBrew Master Configuration
            MASTER = {
                'ENABLED': config.getboolean(section, 'ENABLED'),
                'IP': gethostbyname(config.get(section, 'IP')),
                'PORT': config.getint(section, 'PORT'),
                'PASSPHRASE': config.get(section, 'PASSPHRASE')
            }
        
        elif config.getboolean(section, 'ENABLED'):
            # HomeBrew Client (Repeater) Configuration(s)
            CLIENTS.update({section: {
                'ENABLED': config.getboolean(section, 'ENABLED'),
                'IP': gethostbyname(config.get(section, 'IP')),
                'PORT': config.getint(section, 'PORT'),
                'MASTER_IP': gethostbyname(config.get(section, 'MASTER_IP')),
                'MASTER_PORT': config.getint(section, 'MASTER_PORT'),
                'PASSPHRASE': config.get(section, 'PASSPHRASE'),
                'CALLSIGN': config.get(section, 'CALLSIGN'),
                'RADIO_ID': hex(int(config.get(section, 'RADIO_ID')))[2:].rjust(8,'0').decode('hex'),
                'RX_FREQ': config.get(section, 'RX_FREQ'),
                'TX_FREQ': config.get(section, 'TX_FREQ'),
                'TX_POWER': config.get(section, 'TX_POWER'),
                'COLORCODE': config.get(section, 'COLORCODE'),
                'LATITUDE': config.get(section, 'LATITUDE'),
                'LONGITUDE': config.get(section, 'LONGITUDE'),
                'HEIGHT': config.get(section, 'HEIGHT'),
                'LOCATION': config.get(section, 'LOCATION'),
                'DESCRIPTION': config.get(section, 'DESCRIPTION'),
                'URL': config.get(section, 'URL'),
                'SOFTWARE_ID': config.get(section, 'SOFTWARE_ID'),
                'PACKAGE_ID': config.get(section, 'PACKAGE_ID')
            }})
            
except:
    sys.exit('Could not parse configuration file, exiting...')


#************************************************
#     CONFIGURE THE SYSTEM LOGGER
#************************************************

dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'timed': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'syslog': {
            'format': '%(name)s (%(process)d): %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'class': 'logging.NullHandler'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'console-timed': {
            'class': 'logging.StreamHandler',
            'formatter': 'timed'
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'simple',
            'filename': LOGGER['LOG_FILE'],
        },
        'file-timed': {
            'class': 'logging.FileHandler',
            'formatter': 'timed',
            'filename': LOGGER['LOG_FILE'],
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'syslog',
        }
    },
    'loggers': {
        LOGGER['LOG_NAME']: {
            'handlers': LOGGER['LOG_HANDLERS'].split(','),
            'level': LOGGER['LOG_LEVEL'],
            'propagate': True,
        }
    }
})
logger = logging.getLogger(LOGGER['LOG_NAME'])

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
    if MASTER:
        hbmaster = HBMASTER()
        reactor.listenUDP(MASTER['PORT'], hbmaster, interface=MASTER['IP'])
        
    clients = {}
    for client in CLIENTS:
        if CLIENTS[client]['ENABLED']:
            clients[client] = HBCLIENT(client)
            reactor.listenUDP(CLIENTS[client]['PORT'], clients[client], interface=CLIENTS[client]['IP'])

    reactor.run()