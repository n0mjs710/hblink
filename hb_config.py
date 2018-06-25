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
This module generates the configuration data structure for hblink.py and
assoicated programs that use it. It has been seaparated into a different
module so as to keep hblink.py easeier to navigate. This file only needs
updated if the items in the main configuraiton file (usually hblink.cfg)
change.
'''

import ConfigParser
import sys

from socket import gethostbyname 

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Colin Durbridge, G4EML, Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'GNU GPLv3'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'


def build_config(_config_file):
    config = ConfigParser.ConfigParser()

    if not config.read(_config_file):
        sys.exit('Configuration file \''+_config_file+'\' is not a valid configuration file! Exiting...')        

    CONFIG = {}
    CONFIG['GLOBAL'] = {}
    CONFIG['REPORTS'] = {}
    CONFIG['LOGGER'] = {}
    CONFIG['ALIASES'] = {}
    CONFIG['AMBE'] = {}
    CONFIG['SYSTEMS'] = {}

    try:
        for section in config.sections():
            if section == 'GLOBAL':
                CONFIG['GLOBAL'].update({
                    'PATH': config.get(section, 'PATH'),
                    'PING_TIME': config.getint(section, 'PING_TIME'),
                    'MAX_MISSED': config.getint(section, 'MAX_MISSED')
                })

            elif section == 'REPORTS':
                CONFIG['REPORTS'].update({
                    'REPORT': config.getboolean(section, 'REPORT'),
                    'REPORT_INTERVAL': config.getint(section, 'REPORT_INTERVAL'),
                    'REPORT_PORT': config.getint(section, 'REPORT_PORT'),
                    'REPORT_CLIENTS': config.get(section, 'REPORT_CLIENTS').split(',')
                })

            elif section == 'LOGGER':
                CONFIG['LOGGER'].update({
                    'LOG_FILE': config.get(section, 'LOG_FILE'),
                    'LOG_HANDLERS': config.get(section, 'LOG_HANDLERS'),
                    'LOG_LEVEL': config.get(section, 'LOG_LEVEL'),
                    'LOG_NAME': config.get(section, 'LOG_NAME')
                })

            elif section == 'ALIASES':
                CONFIG['ALIASES'].update({
                    'TRY_DOWNLOAD': config.getboolean(section, 'TRY_DOWNLOAD'),
                    'PATH': config.get(section, 'PATH'),
                    'PEER_FILE': config.get(section, 'PEER_FILE'),
                    'SUBSCRIBER_FILE': config.get(section, 'SUBSCRIBER_FILE'),
                    'TGID_FILE': config.get(section, 'TGID_FILE'),
                    'PEER_URL': config.get(section, 'PEER_URL'),
                    'SUBSCRIBER_URL': config.get(section, 'SUBSCRIBER_URL'),
                    'STALE_TIME': config.getint(section, 'STALE_DAYS') * 86400,
                })

            elif section == 'AMBE':
                CONFIG['AMBE'].update({
                    'EXPORT_IP': gethostbyname(config.get(section, 'EXPORT_IP')),
                    'EXPORT_PORT': config.getint(section, 'EXPORT_PORT'),
                })

            elif config.getboolean(section, 'ENABLED'):
                if config.get(section, 'MODE') == 'CLIENT':
                    CONFIG['SYSTEMS'].update({section: {
                        'MODE': config.get(section, 'MODE'),
                        'ENABLED': config.getboolean(section, 'ENABLED'),
                        'LOOSE': config.getboolean(section, 'LOOSE'),
                        'EXPORT_AMBE': config.getboolean(section, 'EXPORT_AMBE'),
                        'IP': gethostbyname(config.get(section, 'IP')),
                        'PORT': config.getint(section, 'PORT'),
                        'MASTER_IP': gethostbyname(config.get(section, 'MASTER_IP')),
                        'MASTER_PORT': config.getint(section, 'MASTER_PORT'),
                        'PASSPHRASE': config.get(section, 'PASSPHRASE'),
                        'CALLSIGN': config.get(section, 'CALLSIGN').ljust(8)[:8],
                        'RADIO_ID': hex(int(config.get(section, 'RADIO_ID')))[2:].rjust(8,'0').decode('hex'),
                        'RX_FREQ': config.get(section, 'RX_FREQ').ljust(9)[:9],
                        'TX_FREQ': config.get(section, 'TX_FREQ').ljust(9)[:9],
                        'TX_POWER': config.get(section, 'TX_POWER').rjust(2,'0'),
                        'COLORCODE': config.get(section, 'COLORCODE').rjust(2,'0'),
                        'LATITUDE': config.get(section, 'LATITUDE').ljust(8)[:8],
                        'LONGITUDE': config.get(section, 'LONGITUDE').ljust(9)[:9],
                        'HEIGHT': config.get(section, 'HEIGHT').rjust(3,'0'),
                        'LOCATION': config.get(section, 'LOCATION').ljust(20)[:20],
                        'DESCRIPTION': config.get(section, 'DESCRIPTION').ljust(19)[:19],
                        'SLOTS': config.get(section, 'SLOTS'),
                        'URL': config.get(section, 'URL').ljust(124)[:124],
                        'SOFTWARE_ID': config.get(section, 'SOFTWARE_ID').ljust(40)[:40],
                        'PACKAGE_ID': config.get(section, 'PACKAGE_ID').ljust(40)[:40],
                        'GROUP_HANGTIME': config.getint(section, 'GROUP_HANGTIME'),
                        'OPTIONS': config.get(section, 'OPTIONS')
                    }})
                    CONFIG['SYSTEMS'][section].update({'STATS': {
                        'CONNECTION': 'NO',             # NO, RTPL_SENT, AUTHENTICATED, CONFIG-SENT, YES 
                        'PINGS_SENT': 0,
                        'PINGS_ACKD': 0,
                        'NUM_OUTSTANDING': 0,
                        'PING_OUTSTANDING': False,
                        'LAST_PING_TX_TIME': 0,
                        'LAST_PING_ACK_TIME': 0,
                    }})
        
                elif config.get(section, 'MODE') == 'MASTER':
                    CONFIG['SYSTEMS'].update({section: {
                        'MODE': config.get(section, 'MODE'),
                        'ENABLED': config.getboolean(section, 'ENABLED'),
                        'REPEAT': config.getboolean(section, 'REPEAT'),
                        'EXPORT_AMBE': config.getboolean(section, 'EXPORT_AMBE'),
                        'IP': gethostbyname(config.get(section, 'IP')),
                        'PORT': config.getint(section, 'PORT'),
                        'PASSPHRASE': config.get(section, 'PASSPHRASE'),
                        'GROUP_HANGTIME': config.getint(section, 'GROUP_HANGTIME')
                    }})
                    CONFIG['SYSTEMS'][section].update({'CLIENTS': {}})
    
    except ConfigParser.Error, err:
	    print "Cannot parse configuration file. %s" %err
            sys.exit('Could not parse configuration file, exiting...')
        
    return CONFIG





# Used to run this file direclty and print the config,
# which might be useful for debugging
if __name__ == '__main__':
    import sys
    import os
    import argparse
    from pprint import pprint
    
    # Change the current directory to the location of the application
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

    # CLI argument parser - handles picking up the config file from the command line, and sending a "help" message
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', action='store', dest='CONFIG_FILE', help='/full/path/to/config.file (usually hblink.cfg)')
    cli_args = parser.parse_args()


    # Ensure we have a path for the config file, if one wasn't specified, then use the execution directory
    if not cli_args.CONFIG_FILE:
        cli_args.CONFIG_FILE = os.path.dirname(os.path.abspath(__file__))+'/hblink.cfg'
    
    
    pprint(build_config(cli_args.CONFIG_FILE))
