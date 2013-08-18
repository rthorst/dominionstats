# -*- coding: utf-8 -*-

""" Logging utilities. """

import logging
import logging.handlers
import os.path
import sys


def initialize_logging(debug=True):
    script_root = os.path.splitext(sys.argv[0])[0]

    root_logger = logging.getLogger()

    if root_logger.handlers:
        # Handlers already present, don't add more or change config
        return

    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    # Log to a file
    fh = logging.handlers.TimedRotatingFileHandler('/srv/councilroom/logs/councilroom-apps.log', when='midnight')
    formatter = logging.Formatter('%(asctime)s [%(levelname)s/%(process)d/%(name)s] %(message)s')
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    # Put logging output on stdout, too
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s/%(name)s] %(message)s')
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)
