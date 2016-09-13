#!/usr/bin/env python
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

import logging
from logging.config import dictConfig

# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Colin Durbridge, G4EML, Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'


def config_logging(_logger):
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
                'filename': _logger['LOG_FILE'],
            },
            'file-timed': {
                'class': 'logging.FileHandler',
                'formatter': 'timed',
                'filename': _logger['LOG_FILE'],
            },
            'syslog': {
                'class': 'logging.handlers.SysLogHandler',
                'formatter': 'syslog',
            }
        },
        'loggers': {
            _logger['LOG_NAME']: {
                'handlers': _logger['LOG_HANDLERS'].split(','),
                'level': _logger['LOG_LEVEL'],
                'propagate': True,
            }
        }
    })

    return logging.getLogger(_logger['LOG_NAME'])