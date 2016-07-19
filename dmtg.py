#!/usr/bin/env python

__doc__ = '''Module for DMTG (Draft Magic the Gathering) Console Interface'''

import os, optparse
import dmtg
import pprint

### Main Entry Point ###

def main():
    # TODO(JRC): Expand on this section to add options and input error handling.
    parser = optparse.OptionParser(usage='usage: %prog [options] mtg-sets')
    opts, args = parser.parse_args()

    for set_name in [arg.lower() for arg in args]:
        set_cards = dmtg.mtg.fetch_set(set_name)
        dmtg.tts.export_set_deckfiles(set_name, set_cards)
        dmtg.tts.export_set_datafiles(set_name, set_cards)

### Miscellaneous ###

if __name__ == '__main__':
    main()
