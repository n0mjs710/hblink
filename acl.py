###############################################################################
#   Copyright (C) 2018  Cortney T. Buffington, N0MJS <n0mjs@me.com>
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

from dmr_utils.utils import int_id

# Lowest possible Subscirber and/or talkgroup IDs allowed by ETSI standard
ID_MIN = 1
ID_MAX = 16776415


# Checks the supplied ID against the ID given, and the ACL list, and the action
# Returns True if the ID should be allowed, False if it should not be
def acl_check(_id, _acl):
    id = int_id(_id)
    for entry in _acl[1]:
        if entry[0] <= id <= entry[1]:
            return _acl[0]
    return not _acl[0]


def acl_build(_acl):
    if not _acl:
        return(True, set((ID_MIN, ID_MAX)))
    
    acl = set()
    sections = _acl.split(':')
    
    if sections[0] == 'PERMIT':
        action = True
    else:
        action = False
    
    for entry in sections[1].split(','):
        if entry == 'ALL':
            acl.add((ID_MIN, ID_MAX))
            break
            
        elif '-' in entry:
            start,end = entry.split('-')
            start,end = int(start), int(end)
            if (ID_MIN <= start <= ID_MAX) or (ID_MIN <= end <= ID_MAX):
                acl.add((start, end))
            else:
                pass #logger message here
        else:
            id = int(entry)
            if (ID_MIN <= id <= ID_MAX):
                acl.add((id, id))
            else:
                pass #logger message here

    return (action, acl)


if __name__ == '__main__':
    from time import time
    from pprint import pprint
    
    ACL = {
        'SUB': {  
            'K0USY': {
                1: 'PERMIT:1-5,3120101,3120124',
                2: 'DENY:1-5,3120101,3120124'
                }
        },
        'TGID': {
            'GLOBAL': {
                1: 'PERMIT:ALL',
                2: 'DENY:ALL'
                },
            'K0USY': {
                1: 'PERMIT:1-5,3120,31201',
                2: 'DENY:1-5,3120,31201'
                }
            }
    }

    for acl in ACL:
        if 'GLOBAL' not in ACL[acl]:
            ACL[acl].update({'GLOBAL': {1:'PERMIT:ALL',2:'PERMIT:ALL'}})
        for acltype in ACL[acl]:
            for slot in ACL[acl][acltype]:
                ACL[acl][acltype][slot] = acl_build(ACL[acl][acltype][slot])  

    pprint(ACL)
    print

    print(acl_check('\x00\x00\x01', ACL['TGID']['GLOBAL'][1]))
    print(acl_check('\x00\x00\x01', ACL['TGID']['K0USY'][2]))