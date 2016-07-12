#!/usr/bin/env python

__doc__ = '''Module for DMTG (Draft Magic the Gathering) Console Interface'''

import os, optparse
import dmtg

### Main Entry Point ###

def main():
    print dmtg.fetch_set('Conspiracy')

### Miscellaneous ###

if __name__ == '__main__':
    main()
