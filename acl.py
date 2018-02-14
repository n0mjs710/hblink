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
            if (ID_MIN <= id <= ID_MAX) or (ID_MIN <= id <= ID_MAX):
                acl.add((id, id))
            else:
                pass #logger message here

    return (action, acl)


if __name__ == '__main__':
    from time import time
    from pprint import pprint
    
    ACL = {
        'SUB': {  
            'K0USY':  'PERMIT:1-5,3120101,3120124'
        },
        'TGID': {
            'GLOBAL': 'DENY:ALL',
            'K0USY':  'PERMIT:1-5,3120,31201'
            }
    }

    for acl in ACL:
        if 'GLOBAL' not in ACL[acl]:
            ACL[acl].update({'GLOBAL':'PERMIT:ALL'})
        for acltype in ACL[acl]:
            ACL[acl][acltype] = acl_build(ACL[acl][acltype])

    pprint(ACL)
    print

    print(acl_check('\x00\x00\x01', ACL['TGID']['GLOBAL']))
    print(acl_check('\x00\x00\x01', ACL['TGID']['K0USY']))