from __future__ import print_function

import os
import csv
import urllib
from time import time

PATH = './'
PEER_FILE = 'peer_ids.csv'
SUB_FILE = 'subscriber_ids.csv'
STALE_DAYS = 7
STALE_TIME = STALE_DAYS*86400
temp_file = urllib.URLopener()

subscriber_ids = {}
peer_ids = {}
talkgroup_ids = {}

def download_peers():
    try:
        print('Downloading peer ID file')
        temp_file.retrieve('http://www.dmr-marc.net/cgi-bin/trbo-database/datadump.cgi?table=repeaters&format=csv&header=0', PATH+'peer_ids.csv')
    except IOError:
        return 'ID ALIAS MAPPER: Could not download Peer ID file'

def download_subs():
    try:
        print('Downloading subscriber ID file')
        temp_file.retrieve('http://www.dmr-marc.net/cgi-bin/trbo-database/datadump.cgi?table=users&format=csv&header=0', PATH+'subscriber_ids.csv')
    except IOError:
        return 'ID ALIAS MAPPER: Could not download Subscriber ID file'
    
# If our files are more than a week old, get new ones
def try_download():
    now = time()
        
    if os.path.isfile(PATH+PEER_FILE) == True:
        peer_mod_time = os.path.getmtime(PATH+PEER_FILE)
        if peer_mod_time + STALE_TIME < now:
            download_peers()
    else:
        download_peers()

    if os.path.isfile(PATH+SUB_FILE) == True:
        peer_mod_time = os.path.getmtime(PATH+SUB_FILE)
        if peer_mod_time + STALE_TIME < now:
            download_subs()
    else:
        download_subs()
        

def reread_peers():
    global peer_ids
    try:
        with open(PATH+'peer_ids.csv', 'rU') as peer_ids_csv:
            peers = csv.reader(peer_ids_csv, dialect='excel', delimiter=',')
            peer_ids = {}
            for row in peers:
                peer_ids[int(row[0])] = (row[1])
            return 'ID ALIAS MAPPER: Peer data loaded. {} IDs imported'.format(len(peer_ids))
    except IOError:
        return 'ID ALIAS MAPPER: peer_ids.csv not found, Peer aliases will not be available'

def reread_talkgroups():
    global talkgroup_ids
    try:
        with open(PATH+'talkgroup_ids.csv', 'rU') as talkgroup_ids_csv:
            talkgroups = csv.reader(talkgroup_ids_csv, dialect='excel', delimiter=',')
            talkgroup_ids = {}
            for row in talkgroups:
                talkgroup_ids[int(row[1])] = (row[0])
            return 'ID ALIAS MAPPER: Talkgroup data loaded. {} IDs imported'.format(len(talkgroup_ids))
    except IOError:
        return 'ID ALIAS MAPPER: Talkgroup_ids.csv not found, Talkgroup aliases will not be available'


def reread_subscribers():
    global subscriber_ids
    try:
        with open(PATH+'subscriber_ids.csv', 'rU') as subscriber_ids_csv:
            subscribers = csv.reader(subscriber_ids_csv, dialect='excel', delimiter=',')
            subscriber_ids = {}
            for row in subscribers:
                subscriber_ids[int(row[0])] = (row[1])
            return 'ID ALIAS MAPPER: Subscriber data loaded. {} IDs imported'.format(len(subscriber_ids))
    except IOError:
        return 'ID ALIAS MAPPER: Subscriber_ids.csv not found, Subscriber aliases will not be available'

def build_id_dicts():
    try_download()
    reread_subscribers()
    reread_peers()
    reread_talkgroups()

def sub_alias(_sub_id):
    return get_info(int_id(_sub_id), subscriber_ids)
    
def peer_alias(_peer_id):
    return get_info(int_id(_peer_id), peer_ids)

def tg_alias(_tgid):
    return get_info(int_id(_tgid), talkgroup_ids)

# Lookup text data for numeric IDs
#
def get_info(_id, _dict):
    if _id in _dict:
        return _dict[_id]
    return _id