#!/usr/bin/env python
# -*- coding: utf-8 --

from argparse import ArgumentParser
from homoglypher.glyph import Glyph
import os, multiprocessing
from functools import partial
import pandas as pd

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


def make_coocc_table(typeface, size=10, n_cores=4):
    """
    find all character co-occurrences for a font, where a co-occurrence 
    marks characters that are represented by the same glyph

    :param str typeface: filepath to a font file
    :param int size: size of glyphs to draw
    :param int n_cores: cores to use
    :return: character co-occurence matrix
    :rtype: pandas dataframe
    """
    # compile draw_char() as a partial function and send to the pool, 
    # then churn through every possible unicode code point
    to_pool = partial(draw_char, typeface=typeface, size=size)
    with multiprocessing.Pool(n_cores) as pool:
        print("+ Generating bitmaps")
        bitmaps = pool.map(to_pool, [chr(i) for i in range(0x10ffff)])

    # now, draw a whitespace glyph. this process won't track these or 
    # empty bitmaps
    whitespace = draw_char(chr(20), typeface, size)

    # compile the bitmaps into a dataframe and remove whitespace/empty
    # glyphs
    df = pd.DataFrame(enumerate(bitmaps), columns=['DEC', 'BITMAP'])
    df = df[(df['BITMAP'] != whitespace) & (df['BITMAP'] != b'')]

    # oddly, the homoglyphs themselves aren't important, so generate a 
    # remapping dictionary of homoglyph: index position
    remap = {bitmap: idx for idx, bitmap in enumerate(df['BITMAP'].unique())}

    # group the unicode decimals by matching bitmaps
    print("+ Grouping characters")
    groups = (
        df
        .groupby('BITMAP')['DEC']
        .apply(list)
    )
    # transform the groups back into a dataframe and explode the list of 
    # decimals into new rows. then reset the index and remap the 
    # homoglyphs
    groups = pd.DataFrame(groups)
    groups = (
        groups
        .explode('DEC')
        .reset_index()
        .replace(remap)
    )

    # using pd.crosstab(), build a glyph x character table. do a dot 
    # product on the result to get the character co-occurences
    tabulated = pd.crosstab(groups['BITMAP'], groups['DEC'])
    return tabulated.T.dot(tabulated)

def filter_files(args):
    """
    identify files to render

    :param namespace args: command line arguments
    :return: files to render
    :rtype: list
    """
    infiles = os.listdir(args.indir)
    outfiles = os.listdir(args.outdir)
    outfiles = [f[:-4] for f in outfiles]
    to_run = [f for f in infiles if f.startswith('.') == False and f[:-4] not in outfiles]
    print(len(outfiles), "fonts already generated. Generating", len(to_run), "fonts")
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
        coocc = make_coocc_table(path, size=args.size, n_cores=args.ncores)
        outpath = os.path.join(args.outdir, name + '.csv')
        coocc.to_csv(outpath)
