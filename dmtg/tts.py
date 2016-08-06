__doc__ = '''Module for Tabletop Simulator Processing/Exporting Functions'''

import dmtg, mtg
import re, math, string
import os, io, glob
import requests

from PIL import Image
from StringIO import StringIO
from collections import defaultdict

### Module Functions ###

def export_set_deckfiles(set_name, set_cards):
    deckfile_cpf, deckfile_cpd = 69, (10, 7)
    deckfile_count = int(math.ceil(len(set_cards) / float(deckfile_cpf)))
    set_card_dims = ( float('-inf'), float('inf') )

    print('exporting deck file for set %s...' % set_name)

    ## Determine Existence of Local Set Data ##

    deckfile_indir, deckfile_outdir = dmtg.make_set_dirs(set_name)
    if glob.glob(os.path.join(deckfile_outdir, 'magic-%s-*-*.png' % set_name)):
        print('exported local deck file for set %s.' % set_name)
        return

    ## Import the Image Files for All Cards in the Set ##

    for set_card_idx, set_card in enumerate(set_cards):
        dmtg.display_status('card', set_card_idx, len(set_cards))
        set_card_path = os.path.join(deckfile_indir, '%d.jpeg' % set_card_idx)

        if not os.path.isfile(set_card_path):
            set_card_url = mtg.fetch_card_url(set_name, set_card['name'], set_card['mid'])
            set_card_request = requests.get(set_card_url)
            set_card_image = Image.open(StringIO(set_card_request.content))
            set_card_image.save(set_card_path)
        else:
            set_card_image = Image.open(set_card_path)

        set_card_dims = sorted([set_card_dims, set_card_image.size])[-1]
        del set_card_image

    ## Export the Deck Files for the Set ##

    deckfile_dims = tuple(cpd*ppc for cpd, ppc in zip(deckfile_cpd, set_card_dims))

    for deckfile_idx in range(deckfile_count):
        dmtg.display_status('deck file', deckfile_idx, deckfile_count)
        deckfile_cards = deckfile_cpf if deckfile_idx != deckfile_count - 1 \
            else len(set_cards) % deckfile_cpf

        deckfile_name = 'magic-%s-%d-%d.png' % (set_name, deckfile_idx, deckfile_cards)
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

    print('exported new deck file for set %s.' % set_name)

def export_set_datafiles(set_name, set_cards):
    print('exporting data file for set %s...' % set_name)
    datafile_indir, datafile_outdir = dmtg.make_set_dirs(set_name)

    # Import the Data File Templates #

    cardfile_path = os.path.join(dmtg.tmpl_dir, 'tts-cardfile.lua')
    with file(cardfile_path, 'r') as cardfile:
        cardfile_template = string.Template(cardfile.read())

    datafile_path = os.path.join(dmtg.tmpl_dir, 'tts-datafile.lua')
    with file(datafile_path, 'r') as datafile:
        datafile_template = string.Template(datafile.read())

    draftfile_path = os.path.join(dmtg.tmpl_dir, 'tts-draftfile.lua')
    with file(draftfile_path, 'r') as draftfile:
        draftfile_template = string.Template(draftfile.read())

    # Import Special Data Set Files #

    set_mods = ''
    modfile_path = os.path.join(dmtg.lua_dir, '%s.lua' % set_name)
    if os.path.isfile(modfile_path):
        with file(modfile_path, 'r') as modfile:
            set_mods = modfile.read()

    # Export the Data Strings for Each Card #

    set_card_strs = []
    for set_card in set_cards:
        set_card_str = cardfile_template.substitute(
            card_id=set_card['id'],
            card_name='"%s"' % set_card['name'],
            card_type='"%s"' % set_card['type'],
            card_rules='"%s"' % set_card['rules'].replace('"', '\\"'),
            card_colors=','.join('"%s"' % scc for scc in set_card['colors']),
            card_cost=set_card['cost'],
            card_rarity='"%s"' % set_card['rarity'],
        )

        set_card_strs.append(set_card_str)

    set_data = datafile_template.substitute(
        set_name=set_name.lower(),
        set_cards=',\n  '.join(scs.replace('\n', '') for scs in set_card_strs),
        set_mods=set_mods,
    )

    # Export the Data Files for the Set #

    setfile_name = 'magic-%s.lua' % set_name.lower()
    setfile_path = os.path.join(datafile_outdir, setfile_name)

    with file(setfile_path, 'wb') as setfile:
        setfile.write(draftfile_template.substitute(
            set_name=set_name,
            set_data=set_data,
        ))

    print('exported data file for set %s.' % set_name)
