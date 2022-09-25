#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 05 08:28:33 2022

@author: Hrishikesh Terdalkar
"""

import sys

###############################################################################
# Chandojnanam Evaluation

CHANDOJNANAM_PATH = "/home/hrishirt/git/jnanasangraha/platform/chanda"
sys.path.insert(0, CHANDOJNANAM_PATH)
import chanda


def chandojnanam_identify(text):
    MI = chanda.Chanda(f"{CHANDOJNANAM_PATH}/data")
    lr, vr = MI.identify_from_text(text, verse=True, fuzzy=True)
    return lr, vr


###############################################################################

corpora = ["shantavilasa", "ramaraksha", "rajendrakarnapura", "meghaduta"]
sources = ["", "google.", "tesseract."]

# corpora = ["meghaduta"]
# sources = ["sanskritdocuments"]
# # sources = ["gretil"]

###############################################################################

for corpus in corpora:
    for source in sources:
        answers_file = f"{corpus}/answers.txt"
        source_file = f"{corpus}/{corpus}.wikisource.{source}clean.txt"
        output_file = f"{corpus}/chandojnanam.{source}meters.txt"
        output_result_file = f"{corpus}/chandojnanam.{source}evaluation.txt"
        output_truth_file = f"{corpus}/chandojnanam.{source}actual.txt"

        # answers_file = f"{corpus}/answers.{source}.txt"
        # source_file = f"{corpus}/{corpus}.{source}.txt"
        # output_file = f"{corpus}/chandojnanam.{source}.meters.txt"
        # output_result_file = f"{corpus}/chandojnanam.{source}.evaluation.txt"
        # output_truth_file = f"{corpus}/chandojnanam.{source}.actual.txt"

        with open(answers_file) as f:
            answers = [
                line.split(' + ')
                for line in f.read().split("\n") if line.strip()
            ]
        with open(source_file) as f:
            content = f.read()

        lr, vr = chandojnanam_identify(content)

        with open(output_file, mode="w") as f:
            f.write("\n".join([
                f'{" / ".join(_vr["chanda"][0])} ({_vr["chanda"][1]})'
                for _vr in vr
            ]))

        result = []
        actual = []
        for answer, _vr in zip(answers, vr):
            correct = all([x in _vr['chanda'][0] for x in answer])

            if _vr['chanda'][1] < 4:
                actual.append("0")
            else:
                actual.append("1")

            if _vr['chanda'][1] > 3:
                result.append("1")
            else:
                result.append(
                    f'{" / ".join(_vr["chanda"][0])} ({_vr["chanda"][1]})'
                )

        with open(output_truth_file, "w") as f:
            f.write("\n".join(actual))

        with open(output_result_file, "w") as f:
            f.write("\n".join(result))


###############################################################################
