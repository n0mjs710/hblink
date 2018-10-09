#
# To use this feature, you'll need to copy this, or create a file called
# sub_acl.py that's like this one, with your local parameters in it.
#
# The 'action' May be PERMIT|DENY
# Each entry may be a single radio id, or a hypenated range (e.g. 1-2999)
# Format:
# ACL = 'action:id|start-end|,id|start-end,....'
ACL = 'DENY:0-2999,4000000-4000999'
