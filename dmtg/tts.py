__doc__ = '''Module for Tabletop Simulator Processing/Exporting Functions'''

import re, math
import os, io
import requests

from PIL import Image
from StringIO import StringIO

### Module Constants ###

src_dir = os.path.dirname(os.path.relpath(__file__))
out_dir = os.path.join(os.path.dirname(src_dir), 'out')

### Module Functions ###

def export_set_deckfiles(set_name, set_cards):
    deckfile_cpf = 69
    deckfile_count = int(math.ceil(len(set_cards) / float(deckfile_cpf)))

    deckfile_indir = os.path.join(out_dir, '%s-in' % set_name.lower())
    deckfile_outdir = os.path.join(out_dir, '%s-out' % set_name.lower())
    _make_export_dirs(deckfile_indir, deckfile_outdir)

    ## Import the Image Files for All Cards in the Set ##

    for set_card_idx, set_card in enumerate(set_cards):
        set_card_request = requests.get(set_card['url'])
        set_card_image = Image.open(StringIO(set_card_request.content))

        set_card_path = os.path.join(deckfile_indir, '%d.jpeg' % set_card_idx)
        set_card_image.save(set_card_path)

    ## Export the Deck Files for the Set ##

    for deckfile_idx in range(deckfile_count):
        if deckfile_idx != deckfile_count - 1: deckfile_cards = deckfile_cpf
        else: deckfile_cards = deckfile_count % deckfile_cpf

        deckfile_name = 'magic-%s-%d-%d.png' % (set_name.lower(), deckfile_idx, deckfile_cards)
        deckfile_path = os.path.join(deckfile_outdir, deckfile_name)

        for card_idx in range(deckfile_cards):
            pass

def export_set_datafiles(set_name, set_cards):
    pass

### Module Helpers ###

def _make_export_dirs(*export_dirs):
    for export_dir in export_dirs:
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
