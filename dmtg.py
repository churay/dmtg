#!/usr/bin/env python

__doc__ = '''Module for DMTG (Draft Magic the Gathering) Console Interface'''

import os, optparse
import dmtg

### Main Entry Point ###

def main():
    dmtg.export_set_files('RTR')

### Miscellaneous ###

if __name__ == '__main__':
    main()
