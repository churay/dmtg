__doc__ = '''Module for Magic the Gathering Fetcher/Processor Functions'''

import dmtg
import re, math, copy
import os, sys, csv
import lxml, lxml.html, requests

### Module Functions ###

def fetch_set(set_name):
    fetch_url = 'http://gatherer.wizards.com/Pages/Search/Default.aspx'
    fetch_cpp = 100
    fetch_base_params = {'output': 'compact', 'action': 'advanced',
        'special': 'true', 'set': '+["%s"]' % set_name.upper()}

    any_mana_regex = r'(%s)' % '|'.join(dmtg.card_colors)
    one_mana_regex = r'^%s$' % any_mana_regex
    multi_mana_regex = r'^%s or %s$' % (any_mana_regex, any_mana_regex)

    print('fetching card data for set %s...' % set_name)
    set_cards = []

    ## Determine Existence of Local Set Data ##

    set_indir, set_outdir = dmtg.make_set_dirs(set_name)
    set_path = os.path.join(set_indir, '%s.tsv' % set_name.lower())
    if os.path.isfile(set_path):
        with open(set_path, 'r') as set_file:
            set_tsvfile = csv.DictReader(set_file, delimiter='\t')
            for set_entry in enumerate(set_tsvfile):
                set_entry = set_entry[1]
                set_entry['colors'] = set_entry['colors'].split(',')
                set_entry['colors'] = [c for c in set_entry['colors'] if c != '']
                set_cards.append(set_entry)

        print('fetched local card data for set %s.' % set_name)
        return set_cards

    ## Determine Number of Pages in Set ##

    print('  fetching card set metadata...')

    fetch_first_params = dict(fetch_base_params, **{'page': 0})
    first_result = requests.get(fetch_url, params=fetch_first_params)
    first_htmltree = lxml.html.fromstring(first_result.content)

    set_header = first_htmltree.find_class('termdisplay')[0].text_content()
    set_length = int(re.search(r'^.*\(([0-9]+)\).*', set_header).group(1))
    set_pages = int(math.ceil(set_length / float(fetch_cpp)))

    ## Query Each Page for Cards in Set  ##

    for page_index in range(set_pages):
        dmtg.display_status('page', page_index, set_pages)
        fetch_page_params = dict(fetch_base_params, **{'page': page_index})
        page_result = requests.get(fetch_url, params=fetch_page_params)
        page_htmltree = lxml.html.fromstring(page_result.content)

        for card_index, card_elem in enumerate(page_htmltree.find_class('cardItem')):
            card_name_raw = card_elem[0][0].text_content()
            card_name = unicode(card_name_raw).encode('utf-8').strip()

            card_cost_elem = card_elem[1]
            card_colors, card_cost = set(), 0
            for mana_elem in card_cost_elem:
                mana_type = mana_elem.get('alt').lower()
                if mana_type.isdigit():
                    card_cost += int(mana_type)
                elif re.match(one_mana_regex, mana_type):
                    card_colors.add(mana_type)
                    card_cost += 1
                elif re.match(multi_mana_regex, mana_type):
                    card_colors.update(mana_type.split(' or '))
                    card_cost += 1

            card_type_raw = card_elem[2].text_content()
            card_type = unicode(card_type_raw).encode('utf-8').strip()

            card_rarity_elem = card_elem[5][0]
            card_rarity = ''
            for rarity_elem in card_rarity_elem:
                rarity_set = rarity_elem[0].get('alt')
                if rarity_set.lower() == set_name.lower():
                    card_rarity = re.search(r'^.*rarity=([a-zA-Z]).*$',
                        rarity_elem[0].get('src')).group(1).lower()
                    break

            card_href = card_elem[0][0].get('href')
            card_mid = re.search(r'^.*multiverseid=([0-9]+).*$', card_href).group(1)

            set_cards.append({
                'id': str(fetch_cpp * page_index + card_index),
                'mid': card_mid,
                'name': card_name,
                'colors': list(card_colors),
                'cost': card_cost,
                'type': card_type,
                'rarity': card_rarity,
            })

    ## Save Queried Cards to Local Data File ##

    with open(set_path, 'w+') as set_file:
        set_tsvfile = csv.DictWriter(set_file, delimiter='\t', fieldnames=set_cards[0].keys())
        set_tsvfile.writeheader()
        for set_card in set_cards:
            set_card_dict = copy.copy(set_card)
            set_card_dict['colors'] = ','.join(set_card_dict['colors'])
            set_tsvfile.writerow(set_card_dict)

    print('fetched remote card data for set %s.' % set_name)
    return set_cards

def fetch_card_url(set_name, card_name, card_mid):
    mtgcards_url = 'http://magiccards.info/query'
    mtgwotc_url = 'http://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid='

    ## Attempt to Retrieve High-Res URL ##

    mtgcards_params = {'s': 'cname', 'v': 'card', 'q': '%s e:%s/en' % (card_name, set_name)}
    mtgcards_result = requests.get(mtgcards_url, mtgcards_params)
    mtgcards_htmltree = lxml.html.fromstring(mtgcards_result.content)

    if len(mtgcards_htmltree[1]) >= 7 and mtgcards_htmltree[1][4].tag == 'table':
        card_elem = mtgcards_htmltree[1][6]
        while len(card_elem) > 0:
            card_elem = next(
                (se for se in card_elem.iter() if se.tag == 'img'),
                card_elem[0]
            )
            if card_elem.tag == 'img':
                return card_elem.get('src')

    ## Retrieve Low-Res Dependable URL ##

    return '%s%s' % (mtgwotc_url, card_mid)
