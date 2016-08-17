__doc__ = '''Module for Magic the Gathering Fetcher/Processor Functions'''

import dmtg
import re, math, copy
import os, sys, csv
import lxml, lxml.html, requests

### Module Functions ###

def fetch_set_cards(set_code):
    ## Define Function Constants and Procedures ##

    tokens_url = 'http://magiccards.info/extras.html'

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

    set_nametable = fetch_set_nametable()
    set_name = set_nametable.get(set_code, 'Magic Origins')

    print('fetching card data for set %s...' % set_code)
    set_cards = []

    ## Determine Existence of Local Set Data ##

    set_indir, set_outdir = dmtg.make_set_dirs(set_code)
    set_path = os.path.join(set_indir, '%s.tsv' % set_code.lower())
    if os.path.isfile(set_path):
        with open(set_path, 'r') as set_file:
            set_tsvfile = csv.DictReader(set_file, delimiter='\t')
            for set_entry in set_tsvfile:
                set_entry['colors'] = set_entry['colors'].split(',')
                set_entry['colors'] = [c for c in set_entry['colors'] if c != '']
                set_cards.append(set_entry)

        print('fetched local card data for set %s.' % set_code)
        return set_cards

    ## Fetch External Data for Set Cards ##

    """
    set_fetch_params = {'set': '+["%s"]' % set_code.upper()}

    set_nonbasic_filter = dict(set_fetch_params, **{'type': '+!["Basic"]'})
    set_nonbasic_cards = fetch_filtered_cards(set_nonbasic_filter, 'nonbasic cards')

    set_basic_filter = dict(set_fetch_params, **{'type': '+["Basic"]'})
    set_basic_cards = fetch_filtered_cards(set_basic_filter, 'basic cards')
    """

    print('  fetching set token metadata...')

    set_token_cards = []
    tokens_result = requests.get(tokens_url)
    tokens_htmltree = lxml.html.fromstring(tokens_result.content)[1]

    set_header_elems = tokens_htmltree.xpath('.//h2')
    set_header_index = next((tokens_htmltree.index(e) for e in set_header_elems if
        set_name in e.text_content().lower() or e.text_content().lower() in set_name), None)

    set_token_table_elem = tokens_htmltree[set_header_index + 1]
    for token_index, set_token_row_elem in enumerate(set_token_table_elem[1:]):
        dmtg.display_status('set token', token_index, len(set_token_table_elem) - 1)
        token_name_raw = set_token_row_elem[0].text_content()
        token_type = set_token_row_elem[1].text_content()
        token_ratio = set_token_row_elem[2].text_content()

        token_name = re.search(r'^(.*?)( [0-9\*]+/[0-9\*]+)?$', token_name_raw).group(1)
        token_numerator = re.match(r'^([1-9][0-9]*)/[0-9]+$', token_ratio) and \
            re.search(r'^([1-9][0-9]*)/[0-9]+$', token_ratio).group(1)

        if token_type == 'Token' and token_numerator:
            token_page_uri = set_token_row_elem[0][0].get('href')
            token_page_url = 'http://magiccards.info%s' % token_page_uri

            token_result = requests.get(token_page_url)
            token_htmltree = lxml.html.fromstring(token_result.content)[1]
            token_url = token_htmltree[3].xpath('.//img')[0].get('src')

    set_cards = set_nonbasic_cards

    ## Save Queried Cards to Local Data File ##

    with open(set_path, 'w+') as set_file:
        set_tsvfile = csv.DictWriter(set_file, delimiter='\t', fieldnames=set_cards[0].keys())
        set_tsvfile.writeheader()
        for set_card in set_cards:
            set_card_dict = copy.copy(set_card)
            set_card_dict['colors'] = ','.join(set_card_dict['colors'])
            set_tsvfile.writerow(set_card_dict)

    print('fetched remote card data for set %s.' % set_code)
    return set_cards

def fetch_card_url(set_code, card_name, card_mid):
    mtgcards_url = 'http://magiccards.info/query'
    mtgwotc_url = 'http://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid='

    ## Attempt to Retrieve High-Res URL ##

    mtgcards_result = requests.get(mtgcards_url,
        {'s': 'cname', 'v': 'card', 'q': '%s e:%s/en' % (card_name, set_code)})
    mtgcards_htmltree = lxml.html.fromstring(mtgcards_result.content)

    if len(mtgcards_htmltree[1]) >= 7 and mtgcards_htmltree[1][4].tag == 'table':
        card_elem = mtgcards_htmltree[1][6]
        while len(card_elem) > 0:
            card_elem = next((se for se in card_elem.iter() if se.tag == 'img'),
                card_elem[0])
            if card_elem.tag == 'img':
                return card_elem.get('src')

    ## Retrieve Low-Res Dependable URL ##

    return '%s%s' % (mtgwotc_url, card_mid)

def fetch_set_nametable():
    ## Define Function Constants and Procedures ##
    nametable_url = 'https://en.wikipedia.org/wiki/List_of_Magic:_The_Gathering_sets'

    def to_text(wiki_elem):
        citation_subelems = wiki_elem.xpath('.//sup')
        for citation_subelem in citation_subelems:
            citation_subelem.drop_tree()
        return wiki_elem.text_content()

    ## Initialize Fetching Environment ##

    print('fetching name table for sets...')
    set_nametable = {}

    ## Determine Existence of Local Name Table Data ##

    base_dir = dmtg.make_base_dir()
    nametable_path = os.path.join(base_dir, 'nametable.tsv')
    if os.path.isfile(nametable_path):
        with open(nametable_path, 'r') as nametable_file:
            nametable_tsvfile = csv.DictReader(nametable_file, delimiter='\t')
            for nametable_entry in nametable_tsvfile:
                set_nametable[nametable_entry['code']] = nametable_entry['name']

        print('fetched local name table for sets.')
        return set_nametable

    ## Fetch Data for the Local Name Table ##

    nametable_result = requests.get(nametable_url)
    nametable_htmltree = lxml.html.fromstring(nametable_result.content)

    for table_elem in nametable_htmltree.find_class('wikitable'):
        column_heads = [to_text(che).lower() for che in table_elem[0].xpath('.//th')]

        name_index = dmtg.get_first(column_heads, lambda i, h: h == 'set')
        code_index = dmtg.get_first(column_heads, lambda i, h: 'code' in h.split())
        if name_index is None or code_index is None: continue

        for row_elem in table_elem[2:]:
            row_entry_elems = row_elem.xpath('./td')
            if len(row_elem) == 1: continue

            row_name = to_text(row_entry_elems[name_index]).lower().strip()
            row_code = to_text(row_entry_elems[code_index]).lower().strip()

            set_nametable[row_code] = row_name

    ## Save Queried Data to Local Data File ##

    with open(nametable_path, 'w+') as nametable_file:
        nametable_tsvfile = csv.DictWriter(nametable_file, delimiter='\t', fieldnames=['code', 'name'])
        nametable_tsvfile.writeheader()
        for set_code, set_name in set_nametable.iteritems():
            nametable_tsvfile.writerow({'code': set_code, 'name': set_name})

    print('fetched remote name table for sets.')
    return set_nametable
