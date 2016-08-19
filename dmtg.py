#!/usr/bin/env python

__doc__ = '''Module for DMTG (Draft Magic the Gathering) Console Interface'''

import os, optparse, re
import dmtg

### Main Entry Point ###

def main():
    ## Argument Parsing ##

    parser = optparse.OptionParser(usage='usage: %prog [options] mtg-sets')
    opts, args = parser.parse_args()

    if not args:
        parser.error('usage: %prog [options] mtg-sets')

    draft_list = []
    for arg in args:
        set_codes = re.findall(r'^[a-z0-9]{3}$', arg.lower())
        if not set_codes:
            raise TypeError('All arguments must contain one or more MTG set codes; '
                '%s contains none.' % arg)
        if len(set_codes) not in (1, 3):
            raise TypeError('All arguments must have one or three set codes; '
                'not %d as there are for %s.' % (len(set_codes), arg))

        set_codes = \
            tuple(set_codes) if len(set_codes) == 3 else \
            tuple(set_codes[0] for didx in range(3))
        draft_list.append(set_codes)

    ## Argument Processing ##

    for draft_set_codes in draft_list:
        print('=========================================')
        draft_card_lists, draft_extra_lists = [], []
        for set_code in draft_set_codes:
            set_cards, set_extras = dmtg.mtg.fetch_set_cards(set_code)
            draft_card_lists.append(set_cards)
            draft_extra_lists.append(set_extras)
            dmtg.tts.export_set_deckfiles(set_code, set_cards, set_extras)
        dmtg.tts.export_draft_datafiles(draft_set_codes, draft_card_lists, draft_extra_lists)
        print('=========================================')

### Miscellaneous ###

if __name__ == '__main__':
    main()
