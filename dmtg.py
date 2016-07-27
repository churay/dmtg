#!/usr/bin/env python

__doc__ = '''Module for DMTG (Draft Magic the Gathering) Console Interface'''

import os, optparse
import dmtg

### Main Entry Point ###

def main():
    parser = optparse.OptionParser(usage='usage: %prog [options] mtg-sets')
    opts, args = parser.parse_args()

    if not args:
        parser.error('usage: %prog [options] mtg-sets')

    for set_name in [arg.lower() for arg in args]:
        print('=========================================')
        set_cards = dmtg.mtg.fetch_set(set_name)
        dmtg.tts.export_set_deckfiles(set_name, set_cards)
        dmtg.tts.export_set_datafiles(set_name, set_cards)
        print('=========================================')

### Miscellaneous ###

if __name__ == '__main__':
    main()
