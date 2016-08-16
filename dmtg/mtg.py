__doc__ = '''Module for Magic the Gathering Fetcher/Processor Functions'''

import dmtg
import re, math, copy
import os, sys, csv
import lxml, lxml.html, requests

### Module Functions ###

def fetch_set(set_name):
    ## Define Function Constants and Procedures ##

    def to_utf8(raw_text):
        return unicode(raw_text).encode('utf-8').strip()

    def fetch_filtered_cards(filter_params, filter_subject):
        fetch_cpp = 100
        fetch_url = 'http://gatherer.wizards.com/Pages/Search/Default.aspx'

        any_mana_regex = r'(%s)' % '|'.join(dmtg.card_colors)
        one_mana_regex = r'^%s$' % any_mana_regex
        multi_mana_regex = r'^%s or %s$' % (any_mana_regex, any_mana_regex)

        filter_base_params = dict(filter_params,
            **{'output': 'standard', 'action': 'advanced', 'special': 'true'})

        # Determine Number of Pages in Card List #

        print('  fetching set %s metadata...' % filter_subject)

        fetch_first_params = dict(filter_base_params, **{'page': 0})
        first_result = requests.get(fetch_url, params=fetch_first_params)
        first_htmltree = lxml.html.fromstring(first_result.content)

        first_header = first_htmltree.find_class('termdisplay')[0].text_content()
        filter_length = int(re.search(r'^.*\(([0-9]+)\).*', first_header).group(1))
        filter_page_count = int(math.ceil(filter_length / float(fetch_cpp)))

        # Query Each Filter Page for Cards #

        filter_set_raw = filter_params.get('set', '+[""]').lower()
        filter_set = re.search(r'^\+\["(.*)"\]$', filter_set_raw).group(1)

        filter_cards = []
        for page_index in range(filter_page_count):
            dmtg.display_status('set %s' % filter_subject, page_index, filter_page_count)
            fetch_page_params = dict(filter_base_params, **{'page': page_index})
            page_result = requests.get(fetch_url, params=fetch_page_params)
            page_htmltree = lxml.html.fromstring(page_result.content)

            for card_index, card_elem in enumerate(page_htmltree.find_class('cardItem')):
                card_info_elem = card_elem.find_class('middleCol')[0]

                card_name_elem = card_info_elem.find_class('cardTitle')[0]
                card_name = to_utf8(card_name_elem[0].text_content())

                card_href = card_name_elem[0].get('href')
                card_mid = re.search(r'^.*multiverseid=([0-9]+).*$', card_href).group(1)

                card_type_elem = card_info_elem.find_class('typeLine')[0]
                card_type = to_utf8(card_type_elem.text_content())
                if card_type.find('\r\n') != -1:
                    card_type = card_type[:card_type.index('\r\n')]

                card_rules_elem = card_info_elem.find_class('rulesText')[0]
                card_rules = to_utf8(card_rules_elem.text_content())

                card_cost_elem = card_info_elem.find_class('manaCost')[0]
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

                card_rarity_elem = card_elem.find_class('rightCol')[0]
                card_rarity = 'x'
                for rarity_elem in card_rarity_elem.xpath('.//img'):
                    rarity_id = rarity_elem.get('src').lower()
                    rarity_set = re.search(r'^.*set=([a-z0-9][a-z0-9][a-z0-9]).*$', rarity_id).group(1)
                    if not filter_set or rarity_set == filter_set:
                        card_rarity = re.search(r'^.*rarity=([a-z]).*$', rarity_id).group(1)
                        break

                filter_cards.append({
                    'id': str(fetch_cpp * page_index + card_index + 1),
                    'mid': card_mid,
                    'name': card_name,
                    'type': card_type,
                    'rules': card_rules,
                    'colors': list(card_colors),
                    'cost': card_cost,
                    'rarity': card_rarity,
                })

        return filter_cards

    ## Initialize Fetching Environment ##

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

    ## Fetch External Data for Set Cards ##

    set_fetch_params = {'set': '+["%s"]' % set_name.upper()}

    set_nonbasic_filter = dict(set_fetch_params, **{'type': '+!["Basic"]'})
    set_nonbasic_cards = fetch_filtered_cards(set_nonbasic_filter, 'nonbasic cards')

    set_basic_filter = dict(set_fetch_params, **{'type': '+["Basic"]'})
    set_basic_cards = fetch_filtered_cards(set_basic_filter, 'basic cards')

    set_cards = set_nonbasic_cards

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

    mtgcards_result = requests.get(mtgcards_url,
        {'s': 'cname', 'v': 'card', 'q': '%s e:%s/en' % (card_name, set_name)})
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
