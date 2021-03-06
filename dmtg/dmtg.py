__doc__ = '''Module for DMTG (Draft Magic the Gathering) Globals'''

import os, sys

### Module Constants ###

card_colors = ['green', 'blue', 'red', 'white', 'black']
card_rarities = ['c', 'u', 'r', 'm']

base_dir = os.path.dirname(os.path.relpath(__file__))
lua_dir = os.path.join(os.path.dirname(base_dir), 'lmtg')
out_dir = os.path.join(os.path.dirname(base_dir), 'out')
tmpl_dir = os.path.join(os.path.dirname(base_dir), 'tmpl')

### Module Functions ###

def make_set_dirs(set_code):
    set_indir = os.path.join(out_dir, '%s-in' % set_code)
    set_outdir = os.path.join(out_dir, '%s-out' % set_code)

    for set_dir in (set_indir, set_outdir):
        if not os.path.exists(set_dir):
            os.makedirs(set_dir)

    return set_indir, set_outdir

def display_status(set_code, set_index, set_num):
    sys.stdout.write('\r')
    sys.stdout.write('  fetching %s %d/%d...' % (set_code, set_index+1, set_num))
    if set_index + 1 >= set_num: sys.stdout.write('\n')
    sys.stdout.flush()

def to_utf8(raw_text):
    return unicode(raw_text).encode('utf-8').strip().replace('\xe2\x80\x99', '\'')
