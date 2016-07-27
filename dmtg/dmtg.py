__doc__ = '''Module for DMTG (Draft Magic the Gathering) Globals'''

import os, sys

### Module Constants ###

card_colors = ['green', 'blue', 'red', 'white', 'black']
card_rarities = ['c', 'u', 'r', 'm']

src_dir = os.path.dirname(os.path.relpath(__file__))
out_dir = os.path.join(os.path.dirname(src_dir), 'out')
tmpl_dir = os.path.join(os.path.dirname(src_dir), 'tmpl')

### Module Functions ###

def make_set_dirs(set_name):
    set_indir = os.path.join(out_dir, '%s-in' % set_name)
    set_outdir = os.path.join(out_dir, '%s-out' % set_name)

    for set_dir in (set_indir, set_outdir):
        if not os.path.exists(set_dir):
            os.makedirs(set_dir)

    return set_indir, set_outdir

def display_status(set_name, set_idx, set_num):
    sys.stdout.write('\r')
    sys.stdout.write('  fetching %s %d/%d...' % (set_name, set_idx+1, set_num))
    if set_idx + 1 >= set_num: sys.stdout.write('\n')
    sys.stdout.flush()
