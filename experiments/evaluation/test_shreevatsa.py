#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 05 08:28:33 2022

@author: Hrishikesh Terdalkar
"""

import sys
from indic_transliteration.sanscript import transliterate

###############################################################################
# Shreevatsa Evaluation

SHREEVATSA_PATH = "/home/hrishirt/git/shreevatsa-meters/"
sys.path.insert(0, SHREEVATSA_PATH)
import identifier_pipeline


def shreevatsa_identify(verse):
    MI = identifier_pipeline.IdentifierPipeline()
    result = MI.IdentifyFromText(verse)
    return result


###############################################################################

corpora = ["shantavilasa", "ramaraksha", "rajendrakarnapura", "meghaduta"]
sources = ["", "google.", "tesseract."]

# corpora = ["meghaduta"]
# sources = ["sanskritdocuments", "gretil"]

###############################################################################

for corpus in corpora:
    for source in sources:
        answers_file = f"{corpus}/answers.txt"
        source_file = f"{corpus}/{corpus}.wikisource.{source}clean.txt"
        output_file = f"{corpus}/shreevatsa.{source}meters.txt"
        output_result_file = f"{corpus}/shreevatsa.{source}evaluation.txt"

        # answers_file = f"{corpus}/answers.{source}.txt"
        # source_file = f"{corpus}/{corpus}.{source}.txt"
        # output_file = f"{corpus}/shreevatsa.{source}.meters.txt"
        # output_result_file = f"{corpus}/shreevatsa.{source}.evaluation.txt"

        with open(answers_file) as f:
            answers = [line.split(' + ') for line in f.read().split("\n") if line.strip()]
        with open(source_file) as f:
            verses = [verse.strip() for verse in f.read().split("\n\n") if verse.strip()]

        identified = [
            (transliterate(
                shreevatsa_identify(verse)[1][0],
                'iast',
                'devanagari'
            ) if shreevatsa_identify(verse)[1] else "")
            for verse in verses
        ]

        with open(output_file, mode="w") as f:
            f.write("\n".join(identified))

        result = []
        for answer, shree_answer in zip(answers, identified):
            first_chanda = answer[0]
            if len(answer) > 1:
                result.append(shree_answer)
            else:
                if not shree_answer:
                    result.append("0")
                elif shree_answer.startswith(first_chanda):
                    result.append("1")
                elif first_chanda == "अनुष्टुभ्" and shree_answer == "अनुष्टुप्":
                    result.append("1")
                else:
                    result.append(shree_answer)

        with open(output_result_file, "w") as f:
            f.write("\n".join(result))


###############################################################################
