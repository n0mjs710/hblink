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
    CONFIG['CLIENTS'] = {}
    CONFIG['MASTERS'] = {}

    try:
        for section in config.sections():
            if section == 'GLOBAL':
                
                # Process GLOBAL items in the configuration
                CONFIG['GLOBAL'].update({
                    'PATH': config.get(section, 'PATH')
                })

            elif section == 'LOGGER':
                # Process LOGGER items in the configuration
                CONFIG['LOGGER'].update({
                    'LOG_FILE': config.get(section, 'LOG_FILE'),
                    'LOG_HANDLERS': config.get(section, 'LOG_HANDLERS'),
                    'LOG_LEVEL': config.get(section, 'LOG_LEVEL'),
                    'LOG_NAME': config.get(section, 'LOG_NAME')
                })

            elif config.getboolean(section, 'ENABLED'):
                # HomeBrew Client (Repeater) Configuration(s)
                if config.get(section, 'MODE') == 'CLIENT':
                    CONFIG['CLIENTS'].update({section: {
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
                    CONFIG['CLIENTS'][section].update({'STATS': {
                        'CONNECTED': False,
                        'PINGS_SENT': 0,
                        'PINGS_ACKD': 0,
                        'PING_OUTSTANDING': False,
                        'LAST_PING_TX_TIME': 0,
                        'LAST_PING_ACK_TIME': 0,
                    }})
        
                elif config.get(section, 'MODE') == 'MASTER':
                    # HomeBrew Master Configuration
                    CONFIG['MASTERS'].update({section: {
                        'ENABLED': config.getboolean(section, 'ENABLED'),
                        'IP': gethostbyname(config.get(section, 'IP')),
                        'PORT': config.getint(section, 'PORT'),
                        'PASSPHRASE': config.get(section, 'PASSPHRASE')
                    }})
    
    except:
        sys.exit('Could not parse configuration file, exiting...')
        
    return CONFIG