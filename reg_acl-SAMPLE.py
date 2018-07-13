#
# Used to limit HomeBrew repeater Protocol registrations.
#
# If this is the SAMPLE file, you'll need to made a copy or start from scratch
# with one called reg_acl.py
#
# The 'action' May be PERMIT|DENY
# Each entry may be a single radio id, or a hypenated range (e.g. 1-2999)
# Format:
# ACL = 'action:id|start-end|,id|start-end,....'
ACL = 'DENY:1'
