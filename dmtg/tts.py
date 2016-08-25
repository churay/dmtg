__doc__ = '''Module for Tabletop Simulator Processing/Exporting Functions'''

import dmtg, mtg
import re, math, string
import os, io, glob
import requests

from PIL import Image
from StringIO import StringIO
from collections import defaultdict

### Module Functions ###

def export_set_deckfiles(set_code, set_cards, set_extras):
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
    if glob.glob(os.path.join(deckfile_outdir, 'cards-*-*.png')) and \
            glob.glob(os.path.join(deckfile_outdir, 'extras-*-*.png')):
        print('exported local deck file for set %s.' % set_code)
        return

    ## Export Deck Files for All Cards/Extras ##

    set_card_dims = import_set_images(set_cards, 'cards')
    set_extra_dims = import_set_images(set_extras, 'extras')

    export_set_deckfiles(set_cards, set_card_dims, 'cards')
    export_set_deckfiles(set_extras, set_card_dims, 'extras')

    print('exported new deck file for set %s.' % set_code)

def export_draft_datafiles(draft_set_codes, draft_card_lists, draft_extra_lists):
    draft_code = '-'.join(draft_set_codes)

    print('exporting data file for draft %s...' % draft_code)
    base_indir, base_outdir = dmtg.make_set_dirs('base')

    # Import the Data File Templates #

    datafile_templates = {}
    for template_path in glob.glob(os.path.join(dmtg.tmpl_dir, '*.lua')):
        template_name = os.path.splitext(os.path.basename(template_path))[0]
        with file(template_path, 'r') as template_file:
            datafile_templates[template_name] = string.Template(template_file.read())

    # Remove Redundant Sets from Draft #

    set_codes = list(set(draft_set_codes))
    set_card_lists = [draft_card_lists[draft_set_codes.index(sc)] for sc in set_codes]
    set_extra_lists = [draft_extra_lists[draft_set_codes.index(sc)] for sc in set_codes]

    # Import Special Data Files for Draft Sets #

    set_mods_list = []
    for set_code in set_codes:
        set_modfile_path = os.path.join(dmtg.lua_dir, '%s.lua' % set_code)
        if os.path.isfile(set_modfile_path):
            with file(set_modfile_path, 'r') as set_modfile:
                set_mods_list.append(set_modfile.read())
        else:
            set_mods_list.append('')

    # Export the Data for Each Card/Extra in Draft Sets #

    set_data_list = []
    for set_code, set_cards, set_extras, set_mods in \
            zip(set_codes, set_card_lists, set_extra_lists, set_mods_list):
        set_card_strs = []
        for set_card in set_cards:
            set_card_strs.append(datafile_templates['card'].substitute(
                card_id=set_card['id'],
                card_name='"%s"' % set_card['name'],
                card_type='"%s"' % set_card['type'],
                card_rules='"%s"' % set_card['rules'].replace('"', '\\"'),
                card_colors=','.join('"%s"' % scc for scc in set_card['colors']),
                card_cost=set_card['cost'],
                card_rarity='"%s"' % set_card['rarity'],
            ))

        set_extra_strs = []
        for set_extra in set_extras:
            set_extra_strs.append(datafile_templates['card'].substitute(
                card_id=set_extra['id'],
                card_name='"%s"' % set_extra['name'],
                card_type='"%s"' % set_extra['type'],
                card_rules='"%s"' % set_extra['rules'].replace('"', '\\"'),
                card_colors=','.join('"%s"' % sec for sec in set_extra['colors']),
                card_cost=set_extra['cost'],
                card_rarity='"%s"' % set_extra['rarity'],
            ))

        set_data_list.append(datafile_templates['set'].substitute(
            set_code=set_code.lower(),
            set_cards=',\n  '.join(scs.replace('\n', '') for scs in set_card_strs),
            set_extras=',\n  '.join(ses.replace('\n', '') for ses in set_extra_strs),
            set_mods=set_mods,
        ))

    # Export the Amalgamated Draft Data #

    draft_data = StringIO()
    for set_data in set_data_list:
        draft_data.write(set_data)
        draft_data.write('\n')

    # Export the Data Files for the Draft #

    global_draft_data = datafile_templates['tts-global'].substitute(
        draft_data=draft_data.getvalue(),
        set_code_1='"%s"' % draft_set_codes[0],
        set_code_2='"%s"' % draft_set_codes[1],
        set_code_3='"%s"' % draft_set_codes[2],
    )

    for template_name in ('tts-draftbutton', 'tts-setupbutton'):
        draftfile_path = os.path.join(base_outdir, '%s-%s.lua' % (template_name, draft_code))
        with file(draftfile_path, 'wb') as draftfile:
            draftfile.write(datafile_templates[template_name].substitute(
                global_data=global_draft_data
            ))

    print('exported data file for draft %s.' % draft_code)
