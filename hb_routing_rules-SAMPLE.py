RULES = {
    'MASTER-1': {
        'GROUP_HANGTIME': 5,
        'GROUP_VOICE': [
            {'NAME': 'STATEWIDE', 'ACTIVE': False, 'ON': [8,], 'OFF': [9,10], 'SRC_TS': 1, 'SRC_GROUP': 1, 'DST-TYPE': 'CLIENT', 'DST_NET': 'REPEATER-1', 'DST_TS': 2, 'DST_GROUP': 2},
            # When DMRD received on this MASTER, Time Slot 1, Talk Group 1; send to CLIENT-1 on Time Slot 2 Talk Group 2
            # This rule is NOT enabled by default
            # This rule can be enabled by transmitting on TGID 8
            # This rule can be disabled by transmitting on TGID 9 or 10
            # Repeat the above line for as many rules for this IPSC network as you want.
        ]
    },
    'REPEATER-1': {
        'GROUP_HANGTIME': 5,
        'GROUP_VOICE': [
            {'NAME': 'STATEWIDE', 'ACTIVE': False, 'ON': [8,], 'OFF': [9,10], 'SRC_TS': 1, 'SRC_GROUP': 1, 'DST-TYPE': 'MASTER', 'DST_NET': 'MASTER-1', 'DST_TS': 2, 'DST_GROUP': 2},
            # When DMRD received on this CLIENT, Time Slot 1, Talk Group 1; send to MASTER-1 on Time Slot 2 Talk Group 2
            # This rule is NOT enabled by default
            # This rule can be enabled by transmitting on TGID 8
            # This rule can be disabled by transmitting on TGID 9 or 10
            # Repeat the above line for as many rules for this IPSC network as you want.
        ]
    },
}

if __name__ == '__main__':
    from pprint import pprint
    pprint(RULES)