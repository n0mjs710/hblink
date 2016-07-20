# Copyright (c) 2016 Cortney T. Buffington, N0MJS and the K0USY Group. n0mjs@me.com
#
# This work is licensed under the Creative Attribution-NonCommercial-ShareAlike
# 3.0 Unported License.To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

# Known HomeBrew Repeater Message Types
# In message below, "ID" is taken to mean the 4-byte HEX repeater ID string of the repaeter(DMR Radio ID)
RPTL    = 'RPTL'    # Initial LOGIN, RPTL+ID
MSTNAK  = 'MSTNAK'  # Master negatvive ack, MSTNAK+ID
MSTACK  = 'MSTACK'  # Master acknowledgement, MSTACK+ID
                    #   if in response to a login, MSTACK+ID+(random 32-bit integer (as a string))
RPTK    = 'RPTK'    # See explantation elsewhere about passphrase, ID and SHA-256 hash!
MSTPING = 'MSTPING' # From the repeater, MSTPING+ID
RPTPONG = 'MSTPONG' # From the master, MSTPONG+ID
MSTCL   = 'MSTCL'   # From the master, MSTCL+ID indicates close-down of the master
RPTCL   = 'RPTCL'   # From the repeater, RPTCL+ID indicates close-down of the repeater
RPTC    = 'RPTC'    # From the repeater, information packet about the repeater
DMRD    = 'DMRD'    # DMR data, format documented elsewhere