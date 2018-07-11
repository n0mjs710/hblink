#
# Used to limit HomeBrew repeater Protocol registrations.
#
# The 'action' May be PERMIT|DENY
# Each entry may be a single radio id, or a hypenated range (e.g. 1-2999)
# Format:
# ACL = 'action:id|start-end|,id|start-end,....'
ACL = 'DENY:1'