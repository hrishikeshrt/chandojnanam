#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 06 10:37:55 2022

@author: Hrishikesh Terdalkar
"""

import sys
from indic_transliteration.sanscript import transliterate

###############################################################################
# Chandojnanam Identify

CHANDOJNANAM_PATH = "/home/hrishirt/git/jnanasangraha/platform/chanda"
sys.path.insert(0, CHANDOJNANAM_PATH)
import chanda


def chandojnanam_identify(text):
    MI = chanda.Chanda(f"{CHANDOJNANAM_PATH}/data")
    lr, vr = MI.identify_from_text(text, verse=True, fuzzy=True)
    return lr, vr


###############################################################################
# Skrutable Evaluation

SKRUTABLE_PATH = "/home/hrishirt/git/skrutable/"
sys.path.insert(0, SKRUTABLE_PATH)
from meter_identification import MeterIdentifier


def skrutable_identify(verse):
    MI = MeterIdentifier()
    result = MI.identify_meter(
        verse,
        from_scheme='DEV',
        resplit_option='resplit_lite',
        resplit_keep_midpoint=True
    )
    return result


###############################################################################
# Shreevatsa Identify

# SHREEVATSA_PATH = "/home/hrishirt/git/shreevatsa-meters/"
# sys.path.insert(0, SHREEVATSA_PATH)
# import identifier_pipeline


# def shreevatsa_identify(verse):
#     MI = identifier_pipeline.IdentifierPipeline()
#     result = MI.IdentifyFromText(verse)
#     return result


###############################################################################
