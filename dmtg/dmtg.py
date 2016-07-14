__doc__ = '''Module for DMTG (Draft Magic the Gathering) Functions'''

import mtg, tts

### Module Functions ###

def export_set_files(set_name):
    set_cards = mtg.fetch_set(set_name)
    tts.export_set_deckfiles(set_name, set_cards)
    tts.export_set_datafiles(set_name, set_cards)

### Module Helpers ###


