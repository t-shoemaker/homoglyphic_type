#!/usr/bin/env python
# -*- coding: utf-8 --

from argparse import ArgumentParser
from homoglypher.glyph import Glyph
import os, multiprocessing
from functools import partial
import pandas as pd
import numpy as np
from scipy.stats.contingency import crosstab

def draw_char(char, typeface, size):
    """
    generate a bitmap for a character from a font

    :param str char: character to generate
    :param str typeface: typeface to use
    :param int size: size to draw
    :return: base64 encoded bitmap of a character
    :rtype: str
    """
    g = Glyph(char)
    return g.bitmap(typeface, size, 'b64')

def find_glyphs(typeface, size=10, n_cores=4):
    """
    find all character co-occurrences for a font, where a co-occurrence 
    marks characters that are represented by the same glyph

    :param str typeface: filepath to a font file
    :param int size: size of glyphs to draw
    :param int n_cores: cores to use
    :return: table of homoglyph--unicode pairs
    :rtype: pandas dataframe
    """
    # compile draw_char() as a partial function and send to the pool, 
    # then churn through every possible unicode code point
    to_pool = partial(draw_char, typeface=typeface, size=size)
    with multiprocessing.Pool(n_cores) as pool:
        print("+ Generating bitmaps")
        bitmaps = pool.map(to_pool, [chr(i) for i in range(0x10ffff)])

    # now, draw a whitespace glyph and the notdef glyphs. this process 
    # won't track either of these or empty bitmaps (it would be great to 
    # track notdefs, but some fonts are so overloaded with them that 
    # they gum up the rest of this process)
    notdef_1 = draw_char(chr(0), typeface, size)
    notdef_2 = draw_char(chr(0x10ffff), typeface, size)
    whitespace = draw_char(chr(20), typeface, size)

    # compile to a dataframe and do the glyph pruning
    df = pd.DataFrame(enumerate(bitmaps), columns=['DEC', 'BITMAP'])
    df = df[(df['BITMAP'] != notdef_1) & (df['BITMAP'] != notdef_2)]
    df = df[(df['BITMAP'] != whitespace) & (df['BITMAP'] != b'')]

    # oddly, the homoglyphs themselves aren't important, so generate a 
    # remapping dictionary of homoglyph: index position and then remove
    # the homoglyphs for a speed up
    remap = {bitmap: idx for idx, bitmap in enumerate(df['BITMAP'].unique())}
    df = df.replace(remap)

    # group the unicode decimals by matching bitmaps
    print("+ Grouping characters")
    char_groups = (
        df
        .groupby('BITMAP')['DEC']
        .apply(list)
        .to_frame()
    )
    
    # explode the list of decimals into new rows, then reset the index and 
    # remap the homoglyphs
    char_groups = (
        char_groups
        .explode('DEC')
        .reset_index()
    )
    return char_groups

def make_coocc_table(char_groups):
    """
    find all character co-occurrences for a font, where a co-occurence 
    marks characters that are represented by the same glyph

    :param pandas dataframe bitmaps: homoglyph--unicode pairs
    :return: character co-occurrence matrix
    :rtype: pandas dataframe
    """
    print("+ Cross tabulating")
    tabulated = crosstab(
        char_groups['BITMAP'],
        char_groups['DEC'],
        sparse=True
    )
    labels = tabulated[0][1]

    print("+ Generating co-occurrence matrix")
    coocc = tabulated[1].T.dot(tabulated[1])
    return pd.DataFrame(coocc.todense(), index=labels, columns=labels)

def filter_files(args):
    """
    identify files to render

    :param namespace args: command line arguments
    :return: files to render
    :rtype: list
    """
    infiles = os.listdir(args.indir)
    outfiles = os.listdir(args.outdir)
    outfiles = [f[:-4] for f in outfiles if f.startswith('.') is False]
    to_run = [f for f in infiles if f.startswith('.') is False and f[:-4] not in outfiles]
    print(len(outfiles), "font(s) already generated. Generating", len(to_run), "font(s)")
    return to_run

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--indir', type=str)
    parser.add_argument('--outdir', type=str)
    parser.add_argument('--ncores', type=int)
    parser.add_argument('--size', type=int)
    args = parser.parse_args()

    fnames = filter_files(args)

    for f in fnames:
        name = f[:-4]
        print("Finding homoglyphs for", name)
        path = os.path.join(args.indir, f)
        char_groups = find_glyphs(path, size=args.size, n_cores=args.ncores)
        coocc = make_coocc_table(char_groups)
        outpath = os.path.join(args.outdir, name + '.csv')
        coocc.to_csv(outpath)
