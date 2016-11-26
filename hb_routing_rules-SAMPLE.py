'''
THIS EXAMPLE WILL NOT WORK AS IT IS - YOU MUST SPECIFY NAMES AND GROUP IDS!!!
NOTES:
    * GROUP_HANGTIME should be set to the same value as the repeaters in the IPSC network
    * NAME is any name you want, and is used to match reciprocal rules for user-activateion
    * ACTIVE should be set to True if you want the rule active by default, False to be inactive
    * ON and OFF are LISTS of Talkgroup IDs used to trigger this rule off and on. Even if you
        only want one (as shown in the ON example), it has to be in list format. None can be
        handled with an empty list, such as " 'ON': [] ".
    * TO_TYPE is timeout type. If you want to use timers, ON means when it's turned on, it will
        turn off afer the timout period and OFF means it will turn back on after the timout
        period. If you don't want to use timers, set it to anything else, but 'NONE' might be
        a good value for documentation!
    * TIMOUT is a value in minutes for the timout timer. No, I won't make it 'seconds', so don't
        ask. Timers are performance "expense".

DO YOU THINK THIS FILE IS TOO COMPLICATED?
    Because you guys all want more and more features, this file is getting complicated. I have
    dabbled with using a parser to make it easier to build. I'm torn. There is a HUGE benefit
    to having it like it is. This is a python file. Simply running it
    (i.e. "python hb_routing_rules.py) will tell you if there's a syntax error and where. Think
    about that for a few minutes :)
'''

RULES = {
    'MASTER-1': {
        'GROUP_HANGTIME': 5,
        'GROUP_VOICE': [
            {'NAME': 'STATEWIDE', 'DST_NET': 'REPEATER-1', 'SRC_TS': 2, 'SRC_GROUP': 3120, 'DST_TS': 2, 'DST_GROUP': 3120, 'ACTIVE': True, 'TO_TYPE': 'ON', 'TIMEOUT': 2, 'ON': [8,], 'OFF': [9,10]},
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
            {'NAME': 'STATEWIDE', 'DST_NET': 'MASTER-1', 'SRC_TS': 2, 'SRC_GROUP': 3120, 'DST_TS': 2, 'DST_GROUP': 3120, 'ACTIVE': True, 'TO_TYPE': 'ON', 'TIMEOUT': 2, 'ON': [8,], 'OFF': [9,10]},
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
