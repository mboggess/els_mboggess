#!/usr/bin/env python
"""Boilerplate python script."""

from __future__ import print_function
from google.apputils import app
import gflags
import logging
from lib.elsevier_functions import *

FLAGS = gflags.FLAGS

# Flag names are globally defined! So, in general, we need
# to be careful to pick names that are unlikely to be used
# by other libraries.
# If there is a conflict, we'll get an error at import time.

gflags.DEFINE_boolean('debug', False, 'enable debug mode')
gflags.DEFINE_boolean('usage', False, 'print usage information')
gflags.DEFINE_boolean('verbose', False, 'be verbose')

def usage():
    print("Usage")

def main(argv):
    try:
        argv = FLAGS(argv)
    except gflags.FlagsError as e:
        print(e, "\\nUsage: ", sys.argv[0], " ARGS\\n", FLAGS)

    els_main_init(FLAGS.usage, FLAGS.debug)

    debug(FLAGS.debug, "non-flag arguments: " + ' '.join(argv))
    verbose(FLAGS.verbose, "python template script")


if __name__ == '__main__':
    app.run()
