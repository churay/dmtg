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
    deckfile_cpf, deckfile_cpd = 69, (10, 7)
    deckfile_count = int(math.ceil(len(set_cards) / float(deckfile_cpf)))
    set_card_dims = ( float('inf'), float('inf') )

    deckfile_indir = os.path.join(out_dir, '%s-in' % set_name.lower())
    deckfile_outdir = os.path.join(out_dir, '%s-out' % set_name.lower())
    _make_export_dirs(deckfile_indir, deckfile_outdir)

    ## Import the Image Files for All Cards in the Set ##

    for set_card_idx, set_card in enumerate(set_cards):
        set_card_path = os.path.join(deckfile_indir, '%d.jpeg' % set_card_idx)

        if not os.path.isfile(set_card_path):
            set_card_request = requests.get(set_card['url'])
            set_card_image = Image.open(StringIO(set_card_request.content))
            set_card_image.save(set_card_path)
        else:
            set_card_image = Image.open(set_card_path)

        set_card_dims = sorted([set_card_dims, set_card_image.size])[0]
        del set_card_image

    ## Export the Deck Files for the Set ##

    deckfile_dims = tuple(cpd*ppc for cpd, ppc in zip(deckfile_cpd, set_card_dims))

    for deckfile_idx in range(deckfile_count):
        deckfile_cards = deckfile_cpf if deckfile_idx != deckfile_count - 1 \
            else deckfile_count % deckfile_cpf

        deckfile_name = 'magic-%s-%d-%d.png' % (set_name.lower(), deckfile_idx, deckfile_cards)
        deckfile_path = os.path.join(deckfile_outdir, deckfile_name)
        deckfile_image = Image.new('RGB', deckfile_dims, 'white')

        for card_idx in range(deckfile_cpf * deckfile_idx + deckfile_cards):
            card_path = os.path.join(deckfile_indir, '%d.jpeg' % card_idx)
            card_image = Image.open(card_path)
            deckfile_card_image = card_image if card_image.size == set_card_dims \
                else card_image.resize(set_card_dims)

            card_didx = card_idx % deckfile_cpf
            card_xyidx = (card_didx % deckfile_cpd[0], int(card_didx / float(deckfile_cpd[0])))
            deckfile_image.paste(deckfile_card_image, tuple(cdv * dpc for cdv, dpc in zip(card_xyidx, set_card_dims)))
            del deckfile_card_image, card_image

        deckfile_image.save(deckfile_path)
        del deckfile_image

def export_set_datafiles(set_name, set_cards):
    pass

### Module Helpers ###

def _make_export_dirs(*export_dirs):
    for export_dir in export_dirs:
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
