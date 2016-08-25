__doc__ = '''Module for Magic the Gathering Fetcher/Processor Functions'''

import dmtg
import re, math, copy
import os, sys, csv
import dateutil.parser
import lxml, lxml.html, requests

### Module Functions ###

def fetch_set_cards(set_code):
    ## Define Function Constants and Procedures ##

    card_base_url = 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid='
    tokens_url = 'http://magiccards.info/extras.html'
    default_code = 'm15'

    def to_card_mid(card_url):
        return re.search(r'^.*multiverseid=(\d+).*$', card_url).group(1)

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
        first_request = requests.get(fetch_url, params=fetch_first_params)
        first_htmltree = lxml.html.fromstring(first_request.content)

        first_header = first_htmltree.find_class('termdisplay')[0].text_content()
        filter_length = int(re.search(r'^.*\((\d+)\).*', first_header).group(1))
        filter_page_count = int(math.ceil(filter_length / float(fetch_cpp)))

        # Query Each Filter Page for Cards #

        filter_set_raw = filter_params.get('set', '+[""]').lower()
        filter_set = re.search(r'^\+\["(.*)"\]$', filter_set_raw).group(1)

        filter_cards = []
        for page_index in range(filter_page_count):
            dmtg.display_status('set %s' % filter_subject, page_index, filter_page_count)
            fetch_page_params = dict(filter_base_params, **{'page': page_index})
            page_request = requests.get(fetch_url, params=fetch_page_params)
            page_htmltree = lxml.html.fromstring(page_request.content)

            for card_index, card_elem in enumerate(page_htmltree.find_class('cardItem')):
                card_info_elem = card_elem.find_class('middleCol')[0]

                card_name_elem = card_info_elem.find_class('cardTitle')[0]
                card_name = dmtg.to_utf8(card_name_elem[0].text_content())

                card_href = card_name_elem[0].get('href')
                card_mid = to_card_mid(card_href)

                card_type_elem = card_info_elem.find_class('typeLine')[0]
                card_type = dmtg.to_utf8(card_type_elem.text_content())
                if card_type.find('\r\n') != -1:
                    card_type = card_type[:card_type.index('\r\n')]

                card_rules_elem = card_info_elem.find_class('rulesText')[0]
                card_rules = dmtg.to_utf8(card_rules_elem.text_content())

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
                    rarity_set = re.search(r'^.*set=(\w{3}).*$', rarity_id).group(1)
                    if not filter_set or rarity_set == filter_set:
                        card_rarity = re.search(r'^.*rarity=(\w).*$', rarity_id).group(1)
                        break

                filter_cards.append({
                    'id': str(fetch_cpp * page_index + card_index + 1),
                    'mid': card_mid,
                    'fid': str(0),
                    'url': '',
                    'name': card_name,
                    'type': card_type,
                    'rules': card_rules,
                    'colors': list(card_colors),
                    'cost': card_cost,
                    'rarity': card_rarity,
                })

        return filter_cards

    def finalize_cards(set_cards):
        for card_index, card in enumerate(set_cards, 1):
            card['id'] = card_index

    ## Initialize Fetching Environment ##

    set_metatable = fetch_set_metatable()
    set_metadata = set_metatable.get(set_code, default_code)

    print('fetching card data for set %s...' % set_code)
    set_cards, set_extras = [], []

    ## Determine Existence of Local Set Data ##

    set_indir, set_outdir = dmtg.make_set_dirs(set_code)
    set_cards_path = os.path.join(set_indir, '%s-cards.tsv' % set_code.lower())
    set_extras_path = os.path.join(set_indir, '%s-extras.tsv' % set_code.lower())
    if os.path.isfile(set_cards_path) and os.path.isfile(set_extras_path):
        with open(set_cards_path, 'r') as set_cards_file:
            set_cards_tsvfile = csv.DictReader(set_cards_file, delimiter='\t')
            for set_entry in set_cards_tsvfile:
                set_entry['colors'] = set_entry['colors'].split(',')
                set_entry['colors'] = [c for c in set_entry['colors'] if c != '']
                set_cards.append(set_entry)

        with open(set_extras_path, 'r') as set_extras_file:
            set_extras_tsvfile = csv.DictReader(set_extras_file, delimiter='\t')
            for set_entry in set_extras_tsvfile:
                set_entry['colors'] = set_entry['colors'].split(',')
                set_entry['colors'] = [c for c in set_entry['colors'] if c != '']
                set_extras.append(set_entry)

        print('fetched local card data for set %s.' % set_code)
        return set_cards, set_extras

    ## Fetch External Data for Set Cards ##

    set_fetch_params = {'set': '+["%s"]' % set_code.upper()}

    set_nonbasic_filter = dict(set_fetch_params, **{'type': '+!["Basic"]'})
    set_nonbasic_cards = fetch_filtered_cards(set_nonbasic_filter, 'nonbasic cards')

    set_basic_filter = dict(set_fetch_params, **{'type': '+["Basic"]'})
    set_basic_cards = fetch_filtered_cards(set_basic_filter, 'basic cards')
    if not set_basic_cards:
        default_basic_filter = {'set': '+["%s"]' % default_code, 'type': '+["Basic"]'}
        set_basic_cards = fetch_filtered_cards(default_basic_filter, 'default basic cards')

    set_xform_filter = dict(set_nonbasic_filter, **{'text': '+["transform"]'})
    set_xform_cards = fetch_filtered_cards(set_xform_filter, 'transform cards')

    print('  fecthing two-sided card pairs...')

    set_twosided_cards = []
    for card_index, xform_card in enumerate(set_xform_cards):
        dmtg.display_status('two sided pair', card_index, len(set_xform_cards))

        # NOTE: Skip processing a card if its opposite side has already been seen.
        if any(xform_card['mid'] in (cf['mid'], cb['mid']) for cf, cb in set_twosided_cards):
            continue

        card_url = '%s%s' % (card_base_url, xform_card['mid'])
        card_page = requests.get(card_url)
        card_htmltree = lxml.html.fromstring(card_page.content)[1]

        card_content_elem = card_htmltree.find_class('cardComponentTable')[0]
        card_component_elems = card_content_elem.find_class('cardComponentContainer')
        card_component_elems = [e for e in card_component_elems if len(e) > 0]

        if len(card_component_elems) == 2:
            card_faces = []
            for card_component_elem in card_component_elems:
                card_face_image = next((i for i in card_component_elem.xpath('.//img')
                    if i.get('id') and 'cardImage' in i.get('id')), None)
                card_face_href = card_face_image.get('src')
                card_face_mid = to_card_mid(card_face_href)

                card_face = next((c for c in set_nonbasic_cards
                    if c['mid'] == card_face_mid), None)
                card_faces.append(card_face)

            set_twosided_cards.append(tuple(card_faces))

    print('  fetching set token metadata...')

    set_token_cards = []
    tokens_request = requests.get(tokens_url)
    tokens_htmltree = lxml.html.fromstring(tokens_request.content)[1]

    set_header_elems = tokens_htmltree.xpath('.//h2')
    set_header_index = next((tokens_htmltree.index(e) for e in set_header_elems if
        set_metadata['name'] == e.text_content().lower()), None)
    if not set_header_index:
        set_header_index = next((tokens_htmltree.index(e) for e in set_header_elems if
            set_metatable[default_code]['name'] == e.text_content().lower()), None)

    set_token_table_elem = tokens_htmltree[set_header_index + 1]
    for token_index, set_token_row_elem in enumerate(set_token_table_elem[1:]):
        dmtg.display_status('set token', token_index, len(set_token_table_elem) - 1)
        token_name_raw = set_token_row_elem[0].text_content()
        token_type = set_token_row_elem[1].text_content()
        token_ratio = set_token_row_elem[2].text_content()

        token_name = re.search(r'^(.*?)( [0-9\*]+/[0-9\*]+)?$', token_name_raw).group(1)
        token_has_index = re.match(r'^([1-9][0-9]*)/[0-9]+$', token_ratio)

        if token_type == 'Token' and token_has_index:
            token_page_uri = set_token_row_elem[0][0].get('href')
            token_page_url = 'http://magiccards.info%s' % token_page_uri

            token_request = requests.get(token_page_url)
            token_htmltree = lxml.html.fromstring(token_request.content)[1]
            token_url = token_htmltree[3].xpath('.//img')[0].get('src')

            set_token_cards.append({
                'id': str(len(set_basic_cards) + len(set_token_cards) + 1),
                'mid': '',
                'fid': str(0),
                'url': token_url,
                'name': token_name,
                'type': token_type,
                'rules': '',
                'colors': [],
                'cost': 0,
                'rarity': 't',
            })

    ## Finalize Card Sets and Ordering ##

    set_back_cards = dict((cb['mid'], cb) for cf, cb in set_twosided_cards)

    set_cards = [c for c in set_nonbasic_cards if c['mid'] not in set_back_cards]
    set_extras = set_basic_cards + set_back_cards.values() + set_token_cards

    finalize_cards(set_cards)
    finalize_cards(set_extras)

    for card_front, card_back in set_twosided_cards:
        card_front['fid'] = card_back['id']
        card_back['fid'] = card_front['id']

    ## Save Queried Cards to Local Data File ##

    with open(set_cards_path, 'w+') as set_cards_file:
        set_cards_tsvfile = csv.DictWriter(set_cards_file, delimiter='\t',
            fieldnames=set_cards[0].keys())
        set_cards_tsvfile.writeheader()
        for set_card in set_cards:
            set_card_dict = copy.copy(set_card)
            set_card_dict['colors'] = ','.join(set_card_dict['colors'])
            set_cards_tsvfile.writerow(set_card_dict)

    with open(set_extras_path, 'w+') as set_extras_file:
        set_extras_tsvfile = csv.DictWriter(set_extras_file, delimiter='\t',
            fieldnames=set_extras[0].keys())
        set_extras_tsvfile.writeheader()
        for set_extra in set_extras:
            set_card_dict = copy.copy(set_extra)
            set_card_dict['colors'] = ','.join(set_card_dict['colors'])
            set_extras_tsvfile.writerow(set_card_dict)

    print('fetched remote card data for set %s.' % set_code)
    return set_cards, set_extras

def fetch_card_url(set_code, card_name, card_mid):
    mtgcards_url = 'http://magiccards.info/query'
    mtgwotc_url = 'http://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid='

    ## Attempt to Retrieve High-Res URL ##

    mtgcards_request = requests.get(mtgcards_url,
        {'s': 'cname', 'v': 'card', 'q': '%s e:%s/en' % (card_name, set_code)})
    mtgcards_htmltree = lxml.html.fromstring(mtgcards_request.content)

    if len(mtgcards_htmltree[1]) >= 7 and mtgcards_htmltree[1][4].tag == 'table':
        card_elem = mtgcards_htmltree[1][6]
        while len(card_elem) > 0:
            card_elem = next((se for se in card_elem.iter() if se.tag == 'img'),
                card_elem[0])
            if card_elem.tag == 'img':
                return card_elem.get('src')

    ## Retrieve Low-Res Dependable URL ##

    return '%s%s' % (mtgwotc_url, card_mid)

def fetch_set_metatable():
    ## Define Function Constants and Procedures ##

    metatable_url = 'http://magic.wizards.com/en/game-info/products/card-set-archive'

    ## Initialize Fetching Environment ##

    print('fetching metadata for all sets...')
    set_metatable = {}

    ## Determine Existence of Local Name Table Data ##

    base_indir, base_outdir = dmtg.make_set_dirs('base')
    metatable_path = os.path.join(base_indir, 'metadata.tsv')
    if os.path.isfile(metatable_path):
        with open(metatable_path, 'r') as metatable_file:
            metatable_tsvfile = csv.DictReader(metatable_file, delimiter='\t')
            for metatable_entry in metatable_tsvfile:
                metadata_dict = copy.copy(metatable_entry)
                metadata_dict['release'] = dateutil.parser.parse(metadata_dict['release'])
                set_metatable[metadata_dict['code']] = metadata_dict

        print('fetched local metadata for all sets.')
        return set_metatable

    ## Fetch Data for the Local Name Table ##

    metatable_request = requests.get(metatable_url)
    metatable_htmltree = lxml.html.fromstring(metatable_request.content)[1]

    for block_elem in metatable_htmltree.find_class('card-set-archive-table'):
        block_list_elem = block_elem.xpath('.//ul')[0]

        block_name_raw = block_list_elem.xpath('.//li')[0].text_content().lower()
        block_name = block_name_raw.replace('block', '').strip()
        if 'decks' in block_name_raw:
            continue

        for block_set_elem in block_list_elem.xpath('.//li')[1:]:
            set_name = block_set_elem.find_class('nameSet')[0].text_content().strip()

            set_code_elem = block_set_elem.find_class('icon')[0]
            set_code = '' if len(set_code_elem) == 0 else \
                re.search(r'^.*/(\w{3})_[^/]*\.png$', set_code_elem[0].get('src')).group(1)

            # TODO(JRC): There are a few sets that are broken and don't have
            # a set sizes; these sets are a default size of 200 for now.
            set_size_raw = block_set_elem.find_class('quantity')[0].text_content().strip()
            set_size = re.search(r'^(\d+) cards$', set_size_raw).group(1) if \
                re.match(r'^(\d+) cards$', set_size_raw) else '200'

            set_release_elem = block_set_elem.find_class('releaseDate')[0]
            set_release = dateutil.parser.parse(set_release_elem.text_content().strip())

            if set_code and int(set_size) >= 50:
                set_metatable.setdefault(set_code.lower(), {
                    'name': dmtg.to_utf8(set_name.lower()),
                    'code': set_code.lower(),
                    'block': block_name.lower(),
                    'size': set_size,
                    'release': set_release,
                })

    # NOTE: There are a few mismatches between the names given on this page
    # and those listed on the extras site.  The following code attempts to
    # rectify these differences.
    for set_metadata in set_metatable.values():
        set_metadata['name'] = set_metadata['name'].replace('core set', '').strip()

    ## Save Queried Data to Local Data File ##

    with open(metatable_path, 'w+') as metatable_file:
        metatable_tsvfile = csv.DictWriter(metatable_file, delimiter='\t',
            fieldnames=set_metatable.itervalues().next().keys())
        metatable_tsvfile.writeheader()
        for metatable_entry in set_metatable.values():
            metadata_dict = copy.copy(metatable_entry)
            metadata_dict['release'] = str(metadata_dict['release'])
            metatable_tsvfile.writerow(metadata_dict)

    print('fetched remote metadata for all sets.')
    return set_metatable
