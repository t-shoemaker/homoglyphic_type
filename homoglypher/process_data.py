#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import string
import unicodedata
import pandas as pd
import numpy as np

def get_style(name):
    """split the style from the base name of a font.

    example: times-bold => times, bold

    :param name: font name
    :type name: str
    :returns: base font name and style
    :rtype: tup
    """
    cut_at = 0
    for idx, char in enumerate(name):
        if char in string.punctuation:
            cut_at = idx
            break
    base, style = name[:cut_at], name[cut_at:]
    style = style.replace("-", "")
    if base == '':
        base, style = name, None
    return base, style

class HomoglyphJSON:

    def __init__(self, filename, indir):
        """initialize by loading the data.


        once the data is loaded, assign the name and get the font base and 
        style. finally, make a dataframe record

        :param filename: file to use
        :type filename: str
        :param indir: location of file
        :type indir: str
        """
        path = os.path.join(indir, filename)
        with open(path, 'r') as j:
            self.data = json.load(j)
        self.name = filename.replace(".json", "")
        self.base, self.style = get_style(self.name)
        self.record = self._make_record()

    def _make_record(self):
        """create a dataframe from the json homoglyph data.

        :returns: a table of all homoglyphs in the font
        :rtype: pandas dataframe
        """
        # make a 1xn_group dataframe, where each col has a list of decimals
        df = pd.json_normalize(self.data)
        # transpose it, explode the lists into rows, and rename the column
        df = (
            df
            .T
            .explode(0)
            .rename(columns={0: 'DEC'})
        )
        # for each decimal, find its unicode name and category
        names = []
        categories = []
        for char in df['DEC'].apply(chr):
            try:
                names.append(unicodedata.name(char))
                categories.append(unicodedata.category(char))
            except:
                names.append(None)
                categories.append(None)
        # for each decimal, assign the unicode hex, name, and category; 
        # supply the filename (which will be the index) as well as the base font
        # and its style; record the group in which the decimal appears. a group 
        # translates to a homoglyph. set the index to filename and reorder
        # the columns
        reordered = ['DEC', 'HEX', 'NAME', 'CAT', 'FONT', 'STYLE', 'GROUP']
        df = (
            df
            .assign(
                HEX=df['DEC'].apply(hex),
                NAME=names,
                CAT=categories,
                FILE=self.name,
                FONT=self.base,
                STYLE=self.style,
                GROUP=df.index
            )
            .set_index('FILE')
            .reindex(columns=reordered)
        )
        # finally, assign some datatypes
        df = (
            df
            .assign(
                DEC=df['DEC'].astype(int),
                GROUP=df['GROUP'].astype(int)
            )
        )
        return df

class FontTable:

    def __init__(self, filename, indir):
        """initialize by loading the data.

        once the data is loaded, assign the name and get the font base and style

        :param filename: file to use
        :type filename: str
        :param indir: location of file
        :type indir: str
        """
        path = os.path.join(indir, filename)
        self.coocc = pd.read_csv(path, index_col=0)
        self.name = filename.replace(".csv", "")
        self.base, self.style = get_style(self.name)
        self.n_dec = len(self.coocc.columns)
        self.n_homoglyphs = self._count_homoglyphs()
        self.record = self._make_record()

    def _count_homoglyphs(self):
        """find the number of rows where the sum of row values is over 1.

        rows of this kind have co-occurring characters, i.e. homoglyphs

        :returns: number of homoglyphs in the font
        :rtype: int
        """
        homoglyph_rows = self.coocc[self.coocc.sum(axis=1) > 1]
        return len(homoglyph_rows)

    def _make_record(self):
        """create a small dataframe of high level metadata about the font.

        :returns: a row of metadata
        :rtype: pandas dataframe
        """
        record = pd.DataFrame({
            'BASE': self.base,
            'STYLE': self.style,
            'N_DEC': self.n_dec,
            'N_HOMOGLYPH': self.n_homoglyphs
        }, index=[self.name])
        return record

    @staticmethod
    def _get_homoglyph_group(row):
        """for rows with 2+ entries, return the decimals of each character.

        :param row: a row in the glypyh--unicode decimal table
        :type row: pandas series
        :returns: group of characters with the same glyph
        :rtype: list
        """
        mask = row.to_numpy().nonzero()
        nonzero = row.iloc[mask]
        return nonzero.index.tolist()

    def homoglyph_groups(self):
        """find the unique set of decimal groups for each homoglyph.

        :returns: all homoglyph groups in a font
        :rtype: list
        """
        homoglyphs = self.coocc[self.coocc.sum(axis=1) > 1]
        groups = []
        for dec in homoglyphs.index:
            group = self._get_homoglyph_group(homoglyphs.loc[dec])
            groups.append(group)
        to_tuple = map(tuple, groups)
        return [list(group) for group in set(to_tuple)]

