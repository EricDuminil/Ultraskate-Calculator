#!/usr/bin/env python
import sys
import logging
import os
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, os.path.dirname(__file__))

from ultra_app import app as application
application.secret_key = "Sup3rSecr3t"
