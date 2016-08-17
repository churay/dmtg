__doc__ = '''Module for Tabletop Simulator Processing/Exporting Functions'''

import dmtg, mtg
import re, math, string
import os, io, glob
import requests

from PIL import Image
from StringIO import StringIO
from collections import defaultdict

### Module Functions ###

def export_set_deckfiles(set_code, set_cards, set_extras=[]):
    ## Define Function Constants and Procedures ##

    def import_set_images(subset_cards, subset_name):
        deckfile_indir, deckfile_outdir = dmtg.make_set_dirs(set_code)
        subset_card_dims = (float('-inf'), float('-inf'))

        for set_card_index, set_card in enumerate(subset_cards):
            dmtg.display_status('%s image' % subset_name, set_card_index, len(subset_cards))
            set_card_path = os.path.join(deckfile_indir, '%s-%d.jpeg' % (subset_name, set_card_index))

            if not os.path.isfile(set_card_path):
                set_card_url = set_card['url'] if set_card['url'] != '' else \
                    mtg.fetch_card_url(set_code, set_card['name'], set_card['mid'])
                set_card_request = requests.get(set_card_url)
                set_card_image = Image.open(StringIO(set_card_request.content))
                set_card_image.save(set_card_path)
            else:
                set_card_image = Image.open(set_card_path)

            subset_card_dims = sorted([subset_card_dims, set_card_image.size])[-1]
            del set_card_image

        return subset_card_dims

    def export_set_deckfiles(subset_cards, subset_dims, subset_name):
        deckfile_indir, deckfile_outdir = dmtg.make_set_dirs(set_code)
        deckfile_cpf, deckfile_cpd = 69, (10, 7)
        deckfile_count = int(math.ceil(len(subset_cards) / float(deckfile_cpf)))

        deckfile_dims = tuple(cpd*ppc for cpd, ppc in zip(deckfile_cpd, subset_dims))

        for deckfile_index in range(deckfile_count):
            dmtg.display_status('%s deck file' % subset_name, deckfile_index, deckfile_count)
            deckfile_cards = deckfile_cpf if deckfile_index != deckfile_count - 1 \
                else len(subset_cards) % deckfile_cpf

            deckfile_name = '%s-%d-%d.png' % (subset_name, deckfile_index, deckfile_cards)
            deckfile_path = os.path.join(deckfile_outdir, deckfile_name)
            deckfile_image = Image.new('RGB', deckfile_dims, 'white')

            for card_dindex in range(deckfile_cards):
                card_index = deckfile_cpf * deckfile_index + card_dindex

                card_path = os.path.join(deckfile_indir, '%s-%d.jpeg' % (subset_name, card_index))
                card_image = Image.open(card_path)
                deckfile_card_image = card_image if card_image.size == subset_dims \
                    else card_image.resize(subset_dims)

                deckfile_card_coords = (
                    int(card_dindex % deckfile_cpd[0]) * subset_dims[0],
                    int(card_dindex / float(deckfile_cpd[0])) * subset_dims[1],
                )
                deckfile_image.paste(deckfile_card_image, deckfile_card_coords)
                del deckfile_card_image, card_image

            deckfile_image.save(deckfile_path)
            del deckfile_image

    ## Initialize Exporting Environment ##

    print('exporting deck file for set %s...' % set_code)

    ## Determine Existence of Local Set Data ##

    deckfile_indir, deckfile_outdir = dmtg.make_set_dirs(set_code)
    if glob.glob(os.path.join(deckfile_outdir, 'cards-%s-*-*.png' % set_code)) and \
            glob.glob(os.path.join(deckfile_outdir, 'extras-%s-*-*.png' % set_code)):
        print('exported local deck file for set %s.' % set_code)
        return

    ## Export Deck Files for All Cards/Extras ##

    set_card_dims = import_set_images(set_cards, 'cards')
    set_extra_dims = import_set_images(set_extras, 'extras')

    export_set_deckfiles(set_cards, set_card_dims, 'cards')
    export_set_deckfiles(set_extras, set_card_dims, 'extras')

    print('exported new deck file for set %s.' % set_code)

def export_set_datafiles(set_code, set_cards, set_extras=[]):
    print('exporting data file for set %s...' % set_code)
    datafile_indir, datafile_outdir = dmtg.make_set_dirs(set_code)

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
    modfile_path = os.path.join(dmtg.lua_dir, '%s.lua' % set_code)
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
        set_code=set_code.lower(),
        set_cards=',\n  '.join(scs.replace('\n', '') for scs in set_card_strs),
        set_mods=set_mods,
    )

    # Export the Data Files for the Set #

    setfile_name = 'magic-%s.lua' % set_code.lower()
    setfile_path = os.path.join(datafile_outdir, setfile_name)

    with file(setfile_path, 'wb') as setfile:
        setfile.write(draftfile_template.substitute(
            set_code=set_code,
            set_data=set_data,
        ))

    print('exported data file for set %s.' % set_code)
