import ConfigParser
import sys

from socket import gethostbyname 



def build_config(_config_file):
    config = ConfigParser.ConfigParser()

    if not config.read(_config_file):
        sys.exit('Configuration file \''+_config_file+'\' is not a valid configuration file! Exiting...')        

    CONFIG = {}
    CONFIG['GLOBAL'] = {}
    CONFIG['LOGGER'] = {}
    CONFIG['AMBE'] = {}
    CONFIG['SYSTEMS'] = {}

    try:
        for section in config.sections():
            if section == 'GLOBAL':
                
                # Process GLOBAL items in the configuration
                CONFIG['GLOBAL'].update({
                    'PATH': config.get(section, 'PATH'),
                    'PING_TIME': config.getint(section, 'PING_TIME'),
                    'MAX_MISSED': config.getint(section, 'MAX_MISSED')
                })

            elif section == 'LOGGER':
                # Process LOGGER items in the configuration
                CONFIG['LOGGER'].update({
                    'LOG_FILE': config.get(section, 'LOG_FILE'),
                    'LOG_HANDLERS': config.get(section, 'LOG_HANDLERS'),
                    'LOG_LEVEL': config.get(section, 'LOG_LEVEL'),
                    'LOG_NAME': config.get(section, 'LOG_NAME')
                })
                
            elif section == 'AMBE':
                # Process AMBE Export items in the configuration
                CONFIG['AMBE'].update({
                    'EXPORT_IP': gethostbyname(config.get(section, 'EXPORT_IP')),
                    'EXPORT_PORT': config.getint(section, 'EXPORT_PORT'),
                })

            elif config.getboolean(section, 'ENABLED'):
                # HomeBrew Client (Repeater) Configuration(s)
                if config.get(section, 'MODE') == 'CLIENT':
                    CONFIG['SYSTEMS'].update({section: {
                        'MODE': config.get(section, 'MODE'),
                        'ENABLED': config.getboolean(section, 'ENABLED'),
                        'EXPORT_AMBE': config.getboolean(section, 'EXPORT_AMBE'),
                        'IP': gethostbyname(config.get(section, 'IP')),
                        'PORT': config.getint(section, 'PORT'),
                        'MASTER_IP': gethostbyname(config.get(section, 'MASTER_IP')),
                        'MASTER_PORT': config.getint(section, 'MASTER_PORT'),
                        'PASSPHRASE': config.get(section, 'PASSPHRASE'),
                        'CALLSIGN': config.get(section, 'CALLSIGN').ljust(8),
                        'RADIO_ID': hex(int(config.get(section, 'RADIO_ID')))[2:].rjust(8,'0').decode('hex'),
                        'RX_FREQ': config.get(section, 'RX_FREQ').ljust(9),
                        'TX_FREQ': config.get(section, 'TX_FREQ').ljust(9),
                        'TX_POWER': config.get(section, 'TX_POWER').rjust(2,'0'),
                        'COLORCODE': config.get(section, 'COLORCODE').rjust(2,'0'),
                        'LATITUDE': config.get(section, 'LATITUDE').ljust(9),
                        'LONGITUDE': config.get(section, 'LONGITUDE').ljust(10),
                        'HEIGHT': config.get(section, 'HEIGHT').rjust(3,'0'),
                        'LOCATION': config.get(section, 'LOCATION').ljust(20)[:20],
                        'DESCRIPTION': config.get(section, 'DESCRIPTION').ljust(19)[:19],
                        'SLOTS': config.get(section, 'SLOTS'),
                        'URL': config.get(section, 'URL').ljust(124)[:124],
                        'SOFTWARE_ID': config.get(section, 'SOFTWARE_ID').ljust(40)[:40],
                        'PACKAGE_ID': config.get(section, 'PACKAGE_ID').ljust(40)[:40]
                    }})
                    CONFIG['SYSTEMS'][section].update({'STATS': {
                        'CONNECTION': 'NO',             # NO, RTPL_SENT, AUTHENTICATED, CONFIG-SENT, YES 
                        'PINGS_SENT': 0,
                        'PINGS_ACKD': 0,
                        'PING_OUTSTANDING': False,
                        'LAST_PING_TX_TIME': 0,
                        'LAST_PING_ACK_TIME': 0,
                    }})
        
                elif config.get(section, 'MODE') == 'MASTER':
                    # HomeBrew Master Configuration
                    CONFIG['SYSTEMS'].update({section: {
                        'MODE': config.get(section, 'MODE'),
                        'ENABLED': config.getboolean(section, 'ENABLED'),
                        'REPEAT': config.getboolean(section, 'REPEAT'),
                        'EXPORT_AMBE': config.getboolean(section, 'EXPORT_AMBE'),
                        'IP': gethostbyname(config.get(section, 'IP')),
                        'PORT': config.getint(section, 'PORT'),
                        'PASSPHRASE': config.get(section, 'PASSPHRASE')
                    }})
                    CONFIG['SYSTEMS'][section].update({'CLIENTS': {}})
    
    except ConfigParser.Error, err:
	# Very simple error reporting
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