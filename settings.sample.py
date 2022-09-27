#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sample Settings

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os
import tempfile
from pathlib import Path

###############################################################################
# Paths

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data"
TMP_PATH = Path(tempfile.gettempdir()) / 'CHANDA_TMP'

###############################################################################
# Flask

APPLICATION_NAME = "Sanskrit Meter Identification System"

TEMPLATE_PATH = BASE_DIR / "templates"
STATIC_PATH = BASE_DIR / "static"

# Generate a nice key using secrets.token_urlsafe()
SECRET_KEY = os.environ.get('SECRET_KEY', "super-secret-key")

###############################################################################
# Google OCR

CLIENT_SECRET = BASE_DIR / "client_secret.json"
