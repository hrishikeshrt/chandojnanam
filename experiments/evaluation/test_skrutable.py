#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 05 08:28:33 2022

@author: Hrishikesh Terdalkar
"""

import sys
from indic_transliteration.sanscript import transliterate

###############################################################################
# Skrutable Evaluation

SKRUTABLE_PATH = "/home/hrishirt/git/skrutable/"
sys.path.insert(0, SKRUTABLE_PATH)
from meter_identification import MeterIdentifier


def skrutable_identify(verse):
    MI = MeterIdentifier()
    result = MI.identify_meter(verse, from_scheme='DEV', resplit_option='resplit_lite', resplit_keep_midpoint=True)
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
        output_file = f"{corpus}/skrutable.{source}meters.txt"
        output_result_file = f"{corpus}/skrutable.{source}evaluation.txt"

        # answers_file = f"{corpus}/answers.{source}.txt"
        # source_file = f"{corpus}/{corpus}.{source}.txt"
        # output_file = f"{corpus}/skrutable.{source}.meters.txt"
        # output_result_file = f"{corpus}/skrutable.{source}.evaluation.txt"

        with open(answers_file) as f:
            answers = [line.split(' + ') for line in f.read().split("\n") if line.strip()]
        with open(source_file) as f:
            verses = [verse.strip() for verse in f.read().split("\n\n") if verse.strip()]

        identified = [
            transliterate(skrutable_identify(verse).meter_label, 'iast', 'devanagari')
            for verse in verses
        ]

        with open(output_file, mode="w") as f:
            f.write("\n".join(identified))

        result = []

        print(output_file)
        print(len(answers), len(verses), len(identified))
        assert len(answers) == len(identified)

        for answer, skru_answer in zip(answers, identified):
            first_skru = skru_answer.split()[0]
            first_chanda = answer[0]

            if first_skru == first_chanda:
                result.append("1")
            else:
                if first_skru == "अनुष्टुभ्" and first_chanda == "अनुष्टुप्":
                    result.append("1")
                elif first_skru in ["अज्ञातसमवृत्त", "अज्ञातार्धसमवृत्त", "अज्ञातविषमवृत्त", "न"]:
                    result.append("0")
                elif first_skru == "उपजाति":
                    if "अथ वा" in skru_answer:
                        result.append(skru_answer)
                    elif "अज्ञातम्" in skru_answer:
                        result.append("0")
                    else:
                        result.append(skru_answer)
                else:
                    result.append(skru_answer)

        assert len(result) == len(answers)

        with open(output_result_file, "w") as f:
            f.write("\n".join(result))


###############################################################################
