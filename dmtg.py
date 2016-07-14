#!/usr/bin/env python

__doc__ = '''Module for DMTG (Draft Magic the Gathering) Console Interface'''

import os, optparse
import dmtg
import pprint

### Main Entry Point ###

def main():
    pprint.pprint(dmtg.mtg.fetch_set('RTR'))

### Miscellaneous ###

if __name__ == '__main__':
    main()
