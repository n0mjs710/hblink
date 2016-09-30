BS_VOICE_SYNC = '\x75\x5F\xD7\xDF\x75\xF7'
BS_DATA_SYNC  = '\xDF\xF5\x7D\x75\xDF\x5D'

'''
EMB: CC(4b), PI(1b), LCSS(2b), EMB Parity(9b - QR 16,7,5)
Slot Type: CC(4b), DataType(4), Slot Type Parity(12b - )

'''