__doc__ = '''Module for Magic the Gathering Fetcher/Processor Functions'''

import re, math
import lxml, lxml.html, requests

### Module Functions ###

def fetch_set(set_name):
    base_url = 'http://gatherer.wizards.com/Pages/Search'
    fetch_url = '%s/Default.aspx' % base_url
    fetch_cpp = 100

    fetch_base_params = {'output': 'standard', 'action': 'advanced',
        'set': '+["%s"]' % set_name}

    ## Determine Number of Pages in Set ##

    fetch_first_params = dict(fetch_base_params, **{'page': 0})
    first_result = requests.get(fetch_url, params=fetch_first_params)
    first_htmltree = lxml.html.fromstring(first_result.content)

    set_header = first_htmltree.find_class('termdisplay')[0].text_content()
    set_length = int(re.search(r'^.*\(([0-9]+)\).*', set_header).group(1))
    set_pages = int(math.ceil(set_length / float(fetch_cpp)))

    ## Query Each Page for Cards in Set  ##

    set_cards = {}

    for page_index in range(set_pages):
        fetch_page_params = dict(fetch_base_params, **{'page': page_index})
        page_result = requests.get(fetch_url, params=fetch_page_params)
        page_htmltree = lxml.html.fromstring(page_result.content)

        # TODO(JRC): Extend this behavior so that the images are retrieved
        # in addition to the card names (in 'page_card_elem[0][0]').
        for page_card_elem in page_htmltree.find_class('cardItem'):
            page_card_name_raw = page_card_elem[1][1][0].text_content()
            page_card_name  = unicode(page_card_name_raw).encode('utf-8').strip()

            page_card_img_rurl = page_card_elem[0][1][0].get('src')
            page_card_img_url = '%s/%s' % (base_url, page_card_img_rurl)
            # page_card_result = requests.get(page_card_image_url)

            set_cards[page_card_name] = page_card_img_url

    return set_cards

### Module Helpers ###


