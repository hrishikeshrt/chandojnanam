#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 22:23:37 2021

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os
import re
import csv
import json
import functools

from collections import defaultdict, Counter

import Levenshtein as Lev

from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate

import samskrit_text as skt

# size of LRU cache
MAX_CACHE = 1024

###############################################################################


class Chanda:
    """Chanda Identifier"""
    Y = 'Y'
    R = 'R'
    T = 'T'
    N = 'N'
    B = 'B'
    J = 'J'
    S = 'S'
    M = 'M'
    L = 'L'
    G = 'G'
    SYMBOLS = f'{Y}{R}{T}{N}{B}{J}{S}{M}{L}{G}'
    GANA = {
        Y: f'{L}{G}{G}',
        R: f'{G}{L}{G}',
        T: f'{G}{G}{L}',
        N: f'{L}{L}{L}',
        B: f'{G}{L}{L}',
        J: f'{L}{G}{L}',
        S: f'{L}{L}{G}',
        M: f'{G}{G}{G}'
    }

    def __init__(self, data_path, symbols='यरतनभजसमलग'):
        self.input_map = dict(zip(symbols, self.SYMBOLS))
        self.output_map = dict(zip(self.SYMBOLS, symbols))
        self.ttable_in = str.maketrans(self.input_map)
        self.ttable_out = str.maketrans(self.output_map)
        self.gana = self.GANA.copy()
        self.gana_inv = {
            v: k for k, v in self.gana.items()
        }

        # Data Path
        self.data_path = data_path

        # Definitions
        self.CHANDA = defaultdict(list)
        self.SINGLE_CHANDA = defaultdict(list)
        self.MULTI_CHANDA = defaultdict(list)
        self.JAATI = defaultdict(list)
        self.SPLITS = defaultdict(list)

        # Read Data
        self.read_data()

    ###########################################################################

    @functools.lru_cache(maxsize=MAX_CACHE)
    def mark_lg(self, text):
        """
        Mark Laghu-Guru

        @return:
            Returns a flattened list of Laghu-Guru marks.
        """
        skip_syllables = [skt.AVAGRAHA]
        lg_marks = []
        syllables = skt.get_syllables(text)
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        if not flat_syllables:
            return flat_syllables, lg_marks

        for idx, syllable in enumerate(flat_syllables[:-1]):
            if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
                lg_marks.append('')
                continue
            laghu = (
                skt.is_laghu(syllable) and
                (skt.HALANTA not in flat_syllables[idx+1])
            )
            lg_marks.append(self.L if laghu else self.G)

        # handle the last syllable
        syllable = flat_syllables[-1]
        if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
            lg_marks.append('')
        else:
            lg_marks.append(
                self.L if skt.is_laghu(syllable) else self.G
            )

        return syllables, lg_marks

    # ----------------------------------------------------------------------- #

    def lg_to_gana(self, lg_str):
        """Transform Laghu-Guru string into Gana string"""
        gana = []
        for i in range(0, len(lg_str), 3):
            group = lg_str[i:i+3]
            gana.append(self.gana_inv.get(group, group))
        gana_str = ''.join(gana)

        return gana_str

    def gana_to_lg(self, gana_str):
        """Transform Gana string into Laghu-Guru string"""
        return gana_str.translate(str.maketrans(self.gana))

    # ----------------------------------------------------------------------- #

    def count_matra(self, gana_str):
        """Count matra from a Gana or Laghu-Guru string"""
        lg_str = self.gana_to_lg(gana_str)
        return sum([1 if x == self.L else 2 for x in lg_str])

    ###########################################################################

    def read_jaati(self, file):
        """
        Read Jaati list from CSV

        @format:
            - First column contains number of letters
            - Second column contains name(s) of Jaati
        """
        jaati = defaultdict(list)
        with open(file, 'r') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                letter_count = int(row[0].strip())
                names = [c.strip() for c in row[1].split(',')]
                jaati[letter_count] = names

        self.JAATI.update(jaati)
        return jaati

    def read_chanda_definitions(self, chanda_file):
        """
        Read definitions of Chanda from CSV

        @params:
            - file: path of the CSV file containing Chanda definitions

        @format:
            Chanda definition file should have at least 3 columns
                - First column should contain name(s) of Chanda/VRtta
                - Second column should contain Pada
                - Third column should contain the Gana string
            Remaing columns will be ignored.
        """
        chanda = defaultdict(list)
        multi_chanda = defaultdict(list)
        splits = defaultdict(list)

        chanda_pada = defaultdict(dict)

        with open(chanda_file, 'r') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row[0].strip():
                    continue

                names = tuple([c.strip() for c in row[0].split(',')])
                pada = row[1].strip()
                lakshana = ''.join(row[2].split())
                lakshana = lakshana.translate(self.ttable_in)
                lakshana = self.gana_to_lg(lakshana)
                lakshana = lakshana.replace(
                    '-', f"[{self.L}{self.G}]"
                )
                if pada:
                    chanda_pada[names][pada] = lakshana
                    names = tuple([f'{name} (पाद {pada})' for name in names])
                else:
                    chanda_pada[names]['1'] = lakshana
                    chanda_pada[names]['2'] = lakshana

                if lakshana:
                    chanda[lakshana].extend(names)

        for _chanda_names, _pada_lakshana in chanda_pada.items():
            multi_pada = []
            multi_lakshana = []
            for _pada, _lakshana in _pada_lakshana.items():
                multi_pada.append(_pada)
                multi_lakshana.append(_lakshana)
                if len(multi_pada) == 2:
                    names = tuple([
                        f'{name} (पाद {multi_pada[0]}-{multi_pada[-1]})'
                        for name in _chanda_names
                    ])
                    multi_chanda[''.join(multi_lakshana)].extend(names)
                    splits[''.join(multi_lakshana)].append(multi_lakshana)
                    multi_pada = []
                    multi_lakshana = []

        self.SINGLE_CHANDA.update(chanda)
        self.MULTI_CHANDA.update(multi_chanda)
        self.CHANDA.update(chanda)
        self.CHANDA.update(multi_chanda)
        self.SPLITS.update(splits)
        return chanda

    # ----------------------------------------------------------------------- #

    def read_data(self):
        self.read_jaati(os.path.join(self.data_path, 'chanda_jaati.csv'))
        definition_files = [
            'chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv'
        ]
        for chanda_file in definition_files:
            self.read_chanda_definitions(
                os.path.join(self.data_path, chanda_file)
            )

    # ----------------------------------------------------------------------- #

    def read_examples(self):
        example_file = os.path.join(self.data_path, "examples.json")
        with open(example_file, "r") as f:
            examples = json.load(f)
        return examples

    ###########################################################################

    def process_text(self, text):
        scheme = detect(text)
        if scheme != sanscript.DEVANAGARI:
            devanagari_text = transliterate(text, scheme, sanscript.DEVANAGARI)
        else:
            devanagari_text = text
        lines = []
        for line in skt.split_lines(devanagari_text):
            clean_line = skt.clean(line)
            if clean_line:
                lines.append(clean_line)
        return lines

    ###########################################################################

    @functools.lru_cache(maxsize=MAX_CACHE)
    def transform(
        self, source_line, signature,
        replace_cost=1, delete_cost=1, insert_cost=1, max_diff=3
    ):
        """
        Find possible transformations of source string to fit the signature
        """
        syllables, lg_marks = self.mark_lg(source_line)
        # Note: Can avoid this conversion to save time, if needed
        # Just need to ensure that Laghu-Guru string is passed properly
        lg_signature = self.gana_to_lg(signature)
        lg_str = ''.join(lg_marks)
        ops = Lev.editops(lg_str, lg_signature)
        distance = len(ops)

        # weights can be decided by an external agent
        op_cost = {
            'replace': replace_cost,
            'delete': delete_cost,
            'insert': insert_cost
        }

        cost = sum([op_cost[op[0]] for op in ops])

        if distance > max_diff:
            return distance, None

        idx = 0  # overall index (syllables, lg_marks)
        lg_idx = 0  # index in the lg_str
        op_idx = 0  # index in the list of edit operations

        output = []

        op, spos, dpos = ops[op_idx]

        # ------------------------------------------------------------------- #
        for lid, line in enumerate(syllables):
            output_line = []
            # --------------------------------------------------------------- #
            for wid, word in enumerate(line):
                output_word = []
                # ----------------------------------------------------------- #
                for cid, syllable in enumerate(word):
                    output_syllable = syllable
                    if lg_marks[idx]:
                        if lg_idx == spos:
                            if op[0] == 'i':
                                output_syllable = f'i({lg_signature[dpos]})'
                                output_word.append(output_syllable)
                                op_idx += 1
                                # insertion means we need to continue with
                                # the same syllable but next operation,
                                # so we increment op_idx
                                # Hence the other condition (op[0] != 'i')
                                # cannot be in the 'else' part directly

                            if op_idx < distance:
                                op, spos, dpos = ops[op_idx]

                                if op[0] != 'i':
                                    output_syllable = f'{op[0]}({syllable})'
                                    if op[0] == 'r':
                                        substitute = lg_signature[dpos]
                                        output_syllable += f'[{substitute}]'
                                        laghu = skt.is_laghu(syllable)
                                        if not laghu == (substitute == self.L):
                                            tm = skt.toggle_matra(
                                                syllable
                                            )
                                            if tm:
                                                # toggle was successful
                                                output_syllable += f'{{{tm}}}'
                                op_idx += 1
                                if op_idx < distance:
                                    op, spos, dpos = ops[op_idx]

                        # increase index in Laghu-Guru string if valid mark
                        lg_idx += 1

                    # always increment syllable index
                    idx += 1
                    output_word.append(output_syllable)
                # ----------------------------------------------------------- #
                output_line.append(output_word)
            # --------------------------------------------------------------- #
            output.append(output_line)
        # ------------------------------------------------------------------- #

        return cost, output

    ###########################################################################

    def find_direct_match(self, line, multi=False):
        chanda_dictionary = self.MULTI_CHANDA if multi else self.SINGLE_CHANDA

        syllables, lg_marks = self.mark_lg(skt.clean(line))
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        lg_str = ''.join(lg_marks)
        if not lg_str:
            return None

        found = lg_str in chanda_dictionary

        # try searching by making last Guru
        if not found and lg_str[-1] == self.L:
            lg_str = lg_str[:-1] + self.G
            found = lg_str in chanda_dictionary

            # still not found? revert
            if not found:
                lg_str = lg_str[:-1] + self.L

        chanda = []
        jaati = []
        gana = []
        length = []
        if not multi:
            if found:
                chanda += self.SINGLE_CHANDA.get(lg_str)
            jaati = self.JAATI.get(len(lg_str), self.JAATI[-1])
            gana = [self.lg_to_gana(lg_str)]
            length = [str(len(lg_str))]
        else:
            if found:
                chanda = self.MULTI_CHANDA.get(lg_str)
                jaati = [
                    "(" + ', '.join([
                        ' / '.join(self.JAATI.get(len(split), self.JAATI[-1]))
                        for split in splits
                    ]) + ")"
                    for splits in self.SPLITS.get(lg_str)
                ]
                gana = [
                    f"({', '.join([self.lg_to_gana(s) for s in splits])})"
                    for splits in self.SPLITS.get(lg_str)
                ]
                length = [
                    f"({' + '.join([str(len(s)) for s in splits])})"
                    for splits in self.SPLITS.get(lg_str)
                ]

        match = {
            'found': found,
            'syllables': flat_syllables,
            'lg': lg_marks,
            'gana': gana,
            'chanda': chanda,
            'jaati': jaati,
            'length': length
        }
        return match

    ###########################################################################

    def identify_from_text(self, text, fuzzy=False):
        """
        TODO: Identify using other lines
        Consider their fuzzy matches too
        """
        answer = []
        lines = self.process_text(text)

        for line in lines:
            clean_line = skt.clean(line).strip()
            if not clean_line:
                continue

            answer.append({
                'line': line,
                'result': self.identify_line(line, fuzzy=fuzzy)
            })

        return answer

    # ----------------------------------------------------------------------- #

    def identify_line(self, line, fuzzy=False):
        """
        Identify Chanda if possible from a single text line

        @return:
            - found: boolean indicating if the Chanda was found or not
            - matra: number of matras in the line
            - answer: dictionary containing various details about the line
        """
        lines = self.process_text(line)
        if len(lines) > 1:
            raise ValueError('Input contains more than one line.')
        line = lines[0]

        answer = {}

        direct_match = self.find_direct_match(line)
        multi_match = self.find_direct_match(line, multi=True)

        if direct_match is None:
            return answer

        found = direct_match['found'] or multi_match['found']

        lg_str = ''.join(direct_match['lg'])
        regex_matches = [k for k in self.CHANDA if re.match(f'^{k}$', lg_str)]
        if regex_matches:
            found = True
        is_regex_match = bool(regex_matches)

        matra = self.count_matra(lg_str)

        chanda = []
        jaati = []
        gana = []
        length = []
        if found:
            if direct_match['found']:
                chanda += direct_match['chanda']
                jaati += direct_match['jaati']
                gana += direct_match['gana']
                length += direct_match['length']
            if multi_match['found']:
                chanda += multi_match['chanda']
                jaati += multi_match['jaati']
                gana += multi_match['gana']
                length += multi_match['length']

            if is_regex_match:
                chanda += [
                    c
                    for m in regex_matches
                    for c in self.CHANDA.get(m)
                    if c not in chanda
                ]

        answer['found'] = found
        answer['syllables'] = direct_match['syllables']
        answer['lg'] = [self.output_map.get(c, c) for c in direct_match['lg']]
        answer['gana'] = self.lg_to_gana(lg_str).translate(self.ttable_out)
        answer['display_gana'] = (
            ' / '.join(gana).translate(self.ttable_out)
            if gana else
            answer['gana']
        )
        answer['length'] = len(lg_str)
        answer['display_length'] = (
            ' / '.join(length) if length else answer['length']
        )
        answer['matra'] = matra
        answer['chanda'] = chanda
        answer['jaati'] = jaati
        answer['fuzzy'] = []

        if not found and fuzzy:
            for chanda_lg in self.CHANDA:
                chanda_gana = self.lg_to_gana(chanda_lg)
                cost, suggestion = self.transform(line, chanda_lg)
                if suggestion:
                    output = ', '.join([s for ln in suggestion
                                        for w in ln for s in w])
                    output = suggestion
                    answer['fuzzy'].append(
                        (self.CHANDA[chanda_lg],
                         chanda_gana.translate(self.ttable_out),
                         output,
                         cost)
                    )
            answer['fuzzy'] = sorted(answer['fuzzy'], key=lambda x: x[3])[:5]
        return answer

    ###########################################################################

    def analyse(self, file, fuzzy=True, remove_chars=''):
        """
        Analyses a file and identify Chanda from each line.

        @params:
            file: path of the input file
            remove_chars: characters to be removed

        skt.clean() is called after removing remove_chars.
        Lines are identified using the skt.split_lines() function.
        """
        with open(file, 'r') as f:
            content = f.read().translate(str.maketrans('', '', remove_chars))

        analysis = [
            (line, self.identify_line(line, fuzzy=fuzzy))
            for line in self.process_text(content)
        ]

        hit = 0
        unk = 0
        content = []
        fuzzy_freq = Counter()
        chanda_freq = Counter()
        jaati_freq = Counter()
        gana_freq = Counter()
        matra_freq = Counter()
        for line, line_analysis in analysis:
            if not line_analysis:
                continue
            print([line, line_analysis])

            line_chanda = line_analysis['chanda']
            line_jaati = line_analysis['jaati']
            line_gana = line_analysis['gana']
            line_matra = line_analysis['matra']

            hit += line_analysis['found']
            unk += not(line_analysis['found'])

            matra_freq.update([line_matra])
            if line_chanda:
                line_desc = ' / '.join(line_chanda)
                chanda_freq.update(line_chanda)
            else:
                line_desc = line_gana
                gana_freq.update([line_gana])

            if fuzzy and line_analysis['fuzzy']:
                line_fuzzy = line_analysis['fuzzy'][0][0]
                fuzzy_freq.update(line_fuzzy)

            jaati_freq.update(line_jaati)

            content.append(f"{line_matra:<6}: {line_desc:<20}: {line}")

        with open(f'{file}.chanda', 'w') as f:
            f.write('\n'.join(content))

        with open(f'{file}.analysis', 'w') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        result = {
            'hit': hit,
            'unk': unk,
            'chanda_freq': chanda_freq,
            'fuzzy_freq': fuzzy_freq,
            'matra_freq': matra_freq,
            'jaati_freq': jaati_freq,
            'gana_freq': gana_freq,
        }
        return result


###############################################################################
