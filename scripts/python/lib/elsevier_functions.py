#!/usr/bin/env python

from __future__ import print_function
import sys
import logging
import gflags
from google.apputils import app

def els_main_init(flags_usage, flags_debug):
    """Initialize Elsevier project scripts by handling
    common gflags setup operations related to --debug,
    --verbose, etc. Doing things in this function allows
    less DRY coupling of logic across many scripts."""

    # Process flags that just return something and exit
    if flags_usage:
        usage()
        quit()
    debug(flags_debug, "Enabled DEBUG mode for " + sys.argv[0])
     
def debug(flags_debug, to_print):
    if flags_debug:
      print("[+] ", to_print)

def verbose(flags_verbose, to_print):
    if flags_verbose:
      print("[+] ", to_print)
