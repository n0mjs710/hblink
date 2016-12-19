'''
This is the Access Control List (ACL) file for limiting call
routing/bridging in various hblink.py-based applications. It
is a VERY simple format. The action may be to PERMIT or DENY
and the ACL itself is a list of subscriber IDs that may be
permitted or denied.
'''

ACL_ACTION = "DENY"  # May be PERMIT|DENY
ACL = [
    1,2,3,4,5,6,7,8,9,10,100
    ]