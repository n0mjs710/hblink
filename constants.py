from bitarray import bitarray

BS_VOICE_SYNC = bitarray()
BS_DATA_SYNC  = bitarray()

BS_VOICE_SYNC.frombytes(b'\x75\x5F\xD7\xDF\x75\xF7')
BS_DATA_SYNC.frombytes(b'\xDF\xF5\x7D\x75\xDF\x5D')

# Precomputed EMB values, where CC always = 1, and PI always = 0
BURST_B_EMB   = bitarray('0001001110010001')
BURST_C_EMB   = bitarray('0001011101110100')
BURST_D_EMB   = bitarray('0001011101110100')
BURST_E_EMB   = bitarray('0001010100000111')
BURST_F_EMB   = bitarray('0001000111100010')

'''
EMB: CC(4b), PI(1b), LCSS(2b), EMB Parity(9b - QR 16,7,5)
Slot Type: CC(4b), DataType(4), Slot Type Parity(12b - )

'''