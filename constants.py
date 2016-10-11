from bitarray import bitarray

BS_VOICE_SYNC = bitarray()
BS_DATA_SYNC  = bitarray()

BS_VOICE_SYNC.frombytes(b'\x75\x5F\xD7\xDF\x75\xF7')
BS_DATA_SYNC.frombytes(b'\xDF\xF5\x7D\x75\xDF\x5D')

LCSS_SINGLE_FRAG = bitarray('00')
LCSS_FIRST_FRAG  = bitarray('01')
LCSS_LAST_FRAG   = bitarray('10')
LCSS_CONT_FRAG   = bitarray('11')

'''
EMB: CC(4b), PI(1b), LCSS(2b), EMB Parity(9b - QR 16,7,5)
Slot Type: CC(4b), DataType(4), Slot Type Parity(12b - )

'''