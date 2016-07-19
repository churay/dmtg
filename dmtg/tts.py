__doc__ = '''Module for Tabletop Simulator Processing/Exporting Functions'''

import dmtg
import re, math, string
import os, io
import requests

from PIL import Image
from StringIO import StringIO

### Module Functions ###

def export_set_deckfiles(set_name, set_cards):
    deckfile_cpf, deckfile_cpd = 69, (10, 7)
    deckfile_count = int(math.ceil(len(set_cards) / float(deckfile_cpf)))
    set_card_dims = ( float('inf'), float('inf') )

    deckfile_indir, deckfile_outdir = dmtg.make_set_dirs(set_name)

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

        for card_didx in range(deckfile_cards):
            card_idx = deckfile_cpf * deckfile_idx + card_didx

            card_path = os.path.join(deckfile_indir, '%d.jpeg' % card_idx)
            card_image = Image.open(card_path)
            deckfile_card_image = card_image if card_image.size == set_card_dims \
                else card_image.resize(set_card_dims)

            deckfile_card_coords = (
                int(card_didx % deckfile_cpd[0]) * set_card_dims[0],
                int(card_didx / float(deckfile_cpd[0])) * set_card_dims[1],
            )
            deckfile_image.paste(deckfile_card_image, deckfile_card_coords)
            del deckfile_card_image, card_image

        deckfile_image.save(deckfile_path)
        del deckfile_image

def export_set_datafiles(set_name, set_cards):
    datafile_indir, datafile_outdir = dmtg.make_set_dirs(set_name)

    # Import the Data File Templates #

    datafile_path = os.path.join(dmtg.tmpl_dir, 'tts-datafile.lua')
    with file(datafile_path, 'r') as datafile:
        datafile_template = string.Template(datafile.read())

    cardfile_path = os.path.join(dmtg.tmpl_dir, 'tts-cardfile.lua')
    with file(cardfile_path, 'r') as cardfile:
        cardfile_template = string.Template(cardfile.read())

    # Export the Data Strings for Each Card #

    set_card_strs = []
    for set_card in set_cards:
        set_card_str = cardfile_template.substitute(
            card_id=set_card['id'],
            card_name='"%s"' % set_card['name'],
            card_colors=','.join('"%s"' % scc for scc in set_card['colors']),
            card_cost=set_card['cost'],
            card_rarity='"%s"' % set_card['rarity'],
        )

        set_card_strs.append(set_card_str)

    # Export the Data Files for the Set #

    datafile_name = 'magic-%s.lua' % set_name.lower()
    datafile_path = os.path.join(datafile_outdir, datafile_name)

    with file(datafile_path, 'w') as datafile:
        datafile.write(datafile_template.substitute(
            set_name=set_name.lower(),
            set_cards=',\n  '.join(scs.replace('\n', '') for scs in set_card_strs),
        ))
