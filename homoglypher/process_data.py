#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import string
import unicodedata
import pandas as pd

class HomoglyphJSON:

    def __init__(self, filename, indir):
        """
        initialize by loading the data, then assign the name and get the font base
        and style. finally, make a dataframe record
        """
        path = os.path.join(indir, filename)
        with open(path, 'r') as j:
            self.data = json.load(j)
        self.name = filename.replace(".json", "")
        self.base, self.style = self._style()
        self.record = self._make_record()

    def _style(self):
        """
        split the style from the base name of a font (e.g. times-bold => times, bold)
        """
        cut_at = 0
        filename = self.name
        for idx, char in enumerate(filename):
            if char in string.punctuation:
                cut_at = idx
                break
        base = filename[:cut_at]
        style = filename[cut_at:]
        style = style.replace("-", "")

        if base == '':
            base, style = filename, None
        
        return base, style   
 
    def _make_record(self):
        """
        create a dataframe from the json homoglyph data
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
