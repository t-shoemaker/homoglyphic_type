#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from homoglypher.glyph import Glyph
import os
import multiprocessing
from functools import partial
import pandas as pd
import numpy as np
from scipy.stats.contingency import crosstab

def draw_char(char, typeface, size):
    """generate a bitmap for a character from a font.

    :param char: character to generate
    :type char: str
    :param typeface: filepath, a typeface to use
    :type typeface: str
    :param size: size to draw
    :type size: int
    :returns: base64 encoded bitmap of a character
    :rtype: str
    """
    g = Glyph(char)
    return g.bitmap(typeface, size, 'b64')

def find_glyphs(typeface, size=10, n_cores=4):
    """generate glyphs for all characters in a font and group them by glyph.

    :param typeface: filepath, a typeface to use
    :type typeface: str
    :param size: size to draw
    :type size: int
    :param n_cores: cores to use in multiprocessing
    :type n_cores: int
    :returns: table of glyph--unicode decimal pairs
    :rtype: pandas dataframe
    """
    # compile draw_char() as a partial function and send to the pool, then 
    # churn through every possible unicode code point
    to_pool = partial(draw_char, typeface=typeface, size=size)
    with multiprocessing.Pool(n_cores) as pool:
        print("+ Generating bitmaps")
        bitmaps = pool.map(to_pool, [chr(i) for i in range(0x10ffff)])

    # now, draw a whitespace glyph and the notedef glyphs. this process 
    # won't track these or empty bitmaps (it would be great to track notdefs
    # but they gum up the rest of this process)
    notdef_1 = draw_char(chr(0), typeface, size)
    notdef_2 = draw_char(chr(0x10ffff), typeface, size)
    whitespace = draw_char(chr(20), typeface, size)

    # compile to a dataframe and do the glyph pruning
    df = pd.DataFrame(enumerate(bitmaps), columns=['DEC', 'BITMAP'])
    df = df[(df['BITMAP'] != notdef_1) & (df['BITMAP'] != notdef_2)]
    df = df[(df['BITMAP'] != whitespace) & (df['BITMAP'] != b'')]

    # oddly, the glyphs themselves aren't important, they just mark a pairing, 
    # so generate a remapping dictionary of the glyph: index position and 
    # then remove the glyphs for a speedup
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

    # explode the list of decimals into new rows, then reset the index
    char_groups = (
        char_groups
        .explode('DEC')
        .reset_index()
    )
    return char_groups

def make_coocc_table(char_groups):
    """find all character co-occurrences for a font.

    a co-occurrence marks characters represented by the same glyph

    :param char_groups: glyph--unicode pairs
    :type char_groups: pandas dataframe
    :returns: character co-occurrence matrix
    :rtype: pandas dataframe
    """
    if char_groups.empty:
        return pd.DataFrame(index=['BITMAP'], columns=['DEC'])

    print("+ Cross tabulating")
    tabulated = crosstab(
        char_groups['BITMAP'],
        char_groups['DEC'],
        sparse=True
    )
    labels = tabulated[0][1]

    print("+ Generating co-occurrence matrix")
    coocc = tabulated[1].T.dot(tabulated[1])
    return pd.DataFrame(
        coocc.todense(),
        index=labels,
        columns=labels
    )

def filter_files(indir, outdir):
    """identify files to render.

    :param indir: path, directory of .ttf files
    :type indir: str
    :param outdir: path, directory to output results
    :type outdir: str
    :returns: files to render
    :rtype: list
    """
    infiles = [f for f in os.listdir(indir) if f.startswith('.') is False]
    outfiles = [f[:-4] for f in os.listdir(outdir) if f.startswith('.') is False]
    to_run = [f for f in infiles if f[:-4] not in outfiles]

    print(len(outfiles), "font(s) already generated. Generating", len(to_run), "font(s)")
    return to_run

def main(args):
    """take in a list of .ttf files and send them through the rendering process.

    :param args: command line arguments
    :type args: namespace args
    """
    to_run = filter_files(args.indir, args.outdir)

    for f in to_run:
        name = f[:-4]
        print("Generating glyphs for", name)
        inpath = os.path.join(args.indir, f)
        char_groups = find_glyphs(inpath, size=args.size, n_cores=args.n_cores)
        coocc = make_coocc_table(char_groups)
        outpath = os.path.join(args.outdir, name + ".csv")
        coocc.to_csv(outpath)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '--indir',
        type=str
    )
    parser.add_argument(
        '--outdir',
        type=str
    )
    parser.add_argument(
        '--n_cores',
        type=int
    )
    parser.add_argument(
        '--size',
        type=int
    )
    args = parser.parse_args()
    main(args)
