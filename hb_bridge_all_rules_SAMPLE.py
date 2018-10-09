# ACL Entries
#
# The 'action' May be PERMIT|DENY
# Each entry may be a single radio id, a hypenated range (e.g. 1-2999), or the string 'ALL'.
# if "ALL" is used, you may not include any other ranges or individual IDs.
# Format:
# ACL = 'action:id|start-end|,id|start-end,....'
#
# Sections exist for both TGIDs and Subscriber IDs.
# Sections exist for glboal actions, and per-system actions.
# ***FIRST MATCH EXITS***

# SID -  Subscriber ID section.
# TGID - Talkgroup ID section.
#
# "GLOBAL" affects ALL systems
# "SYSTEM NAME" affects the system in quetion
# ACLs are applied both ingress AND egress
# If you omit GLOBAL or SYSTEM level ACLs, they will be initilzied
# automatically as "PERMIT:ALL"
# Each system (or global) has two sections 1 and 2, which correspond
# to timeslots 1 and 2 respectively
#
# EXAMPLE:
#ACL = {
#    'SID': {
#        'GLOBAL': {
#            1:  'PERMIT:ALL',
#            2:  'PERMIT:ALL'
#        },
#        'LINK': {
#            1:  'DENY:3120121',
#            2:  'PERMIT:ALL'
#        }
#    },
#    'TGID': {
#        'GLOBAL': {
#            1:  'PERMIT:ALL',
#            2:  'PERMIT:ALL'
#        },
#        'LINK': {
#            1:  'DENY:1-5,1616',
#            2:  'PERMIT:3120'
#        }
#    }
#}

ACL = {
    'SID': {
        'GLOBAL': {
            1: 'PERMIT:ALL',
            2: 'PERMIT:ALL'
        }
    },
    'TGID': {
        'GLOBAL': {
            1: 'PERMIT:ALL',
            2: 'PERMIT:ALL'
        }
    }
}

