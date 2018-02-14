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
#
# EXAMPLE:
# ACL = {
#     'SID': {  
#         'K0USY':  'PERMIT:1-5,3120101,3120124'
#     },
#     'TGID': {
#         'GLOBAL': 'PERMIT:ALL',
#         'K0USY':  'DENY:1-5,3120,31201'
#         }
# }

ACL = {
    'SID': {
        'GLOBAL': 'PERMIT:ALL'
    },
    'TGID': {
        'GLOBAL': 'PERMIT:ALL'
    }
}