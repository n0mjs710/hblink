#!/usr/bin/env python
#
###############################################################################
#   Copyright (C) 2017 Mike Zingman N4IRR
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
'''

from __future__ import print_function

# Python modules we need
import sys
from bitarray import bitarray
from bitstring import BitArray
from bitstring import BitString
import struct
from time import time, sleep
from importlib import import_module
from binascii import b2a_hex as ahex
from random import randint
import sys, socket, ConfigParser, thread, traceback
from threading import Lock
from time import time, sleep, clock, localtime, strftime

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet import task

# Things we import from the main hblink module
from hblink import HBSYSTEM, systems, int_id, hblink_handler
from dmr_utils.utils import hex_str_3, hex_str_4, int_id, get_alias
from dmr_utils import decode, bptc, const, golay, qr
import hb_config
import hb_log
import hb_const
from dmr_utils import ambe_utils
from dmr_utils.ambe_bridge import AMBE_HB

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Mike Zingman, N4IRR and Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2017 Mike Zingman N4IRR'
__credits__    = 'Cortney T. Buffington, N0MJS; Colin Durbridge, G4EML, Steve Zingman, N4IRS; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'GNU GPLv3'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'
__status__     = 'pre-alpha'
__version__    = '20170620'

mutex = Lock()  # Used to synchronize Peer I/O in different threads

class TRANSLATE:
    def __init__(self, config_file):
        self.translate = {}
        self.load_config(config_file)
        pass
    def add_rule( self, tg, export_rule):
        self.translate[str(tg)] = export_rule
        #print(int_id(tg), export_rule)
    def delete_rule(self, tg):
        if str(tg) in self.translate:
            del self.translate[str(tg)]
    def find_rule(self, tg, slot):
        if str(tg) in self.translate:
            return self.translate[str(tg)]
        return (tg, slot)
    def load_config(self, config_file):
        print('load config file', config_file)
        pass

# translation structure.  IMPORT_TO translates foreign (TG,TS) to local.  EXPORT_AS translates local (TG,TS) to foreign values
translate = TRANSLATE('config.file')

class HB_BRIDGE(HBSYSTEM):
    
    def __init__(self, _name, _config, _logger):
        HBSYSTEM.__init__(self, _name, _config, _logger)


        self._ambeRxPort = 31003        # Port to listen on for AMBE frames to transmit to all peers
        self._gateway = "127.0.0.1"     # IP address of Analog_Bridge app
        self._gateway_port = 31000      # Port Analog_Bridge is listening on for AMBE frames to decode

        self.load_configuration('HB_Bridge.cfg')

        self.hb_ambe = AMBE_HB(self, _name, _config, _logger, self._ambeRxPort)
        self._sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    def get_globals(self):
        return (subscriber_ids, talkgroup_ids, peer_ids)

    def get_repeater_id(self, import_id):
        if self._config['MODE'] == 'CLIENT':    # only clients have radio_id defined, masters do not
            return self._config['RADIO_ID']
        return import_id

    # Load configuration from file
    def load_configuration( self, _file_name ):
        config = ConfigParser.ConfigParser()
        if not config.read(_file_name):
            sys.exit('Configuration file \''+_file_name+'\' is not a valid configuration file! Exiting...')
        try:
            for section in config.sections():
                if section == 'DEFAULTS':
                    self._ambeRxPort = int(config.get(section, 'fromGatewayPort').split(None)[0])           # Port to listen on for AMBE frames to transmit to all peers
                    self._gateway = config.get(section, 'gateway').split(None)[0]                           # IP address of Analog_Bridge app
                    self._gateway_port = int(config.get(section, 'toGatewayPort').split(None)[0])           # Port Analog_Bridge is listening on for AMBE frames to decode
                if section == 'RULES':
                    for rule in config.items(section):
                        _old_tg, _new_tg, _new_slot = rule[1].split(',')
                        translate.add_rule(hex_str_3(int(_old_tg)), (hex_str_3(int(_new_tg)), int(_new_slot)))

        except ConfigParser.Error, err:
            traceback.print_exc()
            sys.exit('Could not parse configuration file, ' + _file_name + ', exiting...')


    # HBLink callback with DMR data from perr/master.  Send this data to any partner listening
    def dmrd_received(self, _radio_id, _rf_src, _dst_id, _seq, _slot, _call_type, _frame_type, _dtype_vseq, _stream_id, _data):
        _dst_id, _slot = translate.find_rule(_dst_id,_slot)
        _tx_slot = self.hb_ambe.tx[_slot]
        _seq = ord(_data[4])
        _tx_slot.frame_count += 1
        if (_stream_id != _tx_slot.stream_id):
            self.hb_ambe.begin_call(_slot, _rf_src, _dst_id, _radio_id, _tx_slot.cc, _seq, _stream_id)
            _tx_slot.lastSeq = _seq
        if (_frame_type == hb_const.HBPF_DATA_SYNC) and (_dtype_vseq == hb_const.HBPF_SLT_VTERM) and (_tx_slot.type != hb_const.HBPF_SLT_VTERM):
            self.hb_ambe.end_call(_tx_slot)
        if (int_id(_data[15]) & 0x20) == 0:
            _dmr_frame = BitArray('0x'+ahex(_data[20:]))
            _ambe = _dmr_frame[0:108] + _dmr_frame[156:264]
            self.hb_ambe.export_voice(_tx_slot, _seq, _ambe.tobytes())
        else:
            _tx_slot.lastSeq = _seq

    # The methods below are overridden becuse the launchUDP thread can also wite to a master or client async and confuse the master
    # A lock is used to synchronize the two threads so that the resource is protected
    def send_master(self, _packet):
        mutex.acquire()
        HBSYSTEM.send_master(self, _packet)
        mutex.release()
    
    def send_clients(self, _packet):
        mutex.acquire()
        HBSYSTEM.send_clients(self, _packet)
        mutex.release()

############################################################################################################
#      MAIN PROGRAM LOOP STARTS HERE
############################################################################################################

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
        logger.info('SHUTDOWN: HB_Bridge IS TERMINATING WITH SIGNAL %s', str(_signal))
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
        
    
    # HBlink instance creation
    logger.info('HBlink \'HB_Bridge.py\' (c) 2017 Mike Zingman N4IRR, N0MJS - SYSTEM STARTING...')
    logger.info('Version %s', __version__)
    for system in CONFIG['SYSTEMS']:
        if CONFIG['SYSTEMS'][system]['ENABLED']:
            systems[system] = HB_BRIDGE(system, CONFIG, logger)
            reactor.listenUDP(CONFIG['SYSTEMS'][system]['PORT'], systems[system], interface=CONFIG['SYSTEMS'][system]['IP'])
            logger.debug('%s instance created: %s, %s', CONFIG['SYSTEMS'][system]['MODE'], system, systems[system])

    reactor.run()
