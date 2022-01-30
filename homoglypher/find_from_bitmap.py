#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from PIL import Image, ImageFont, ImageDraw
import base64, os, multiprocessing
from functools import partial
import pandas as pd

def bitmap(char, typeface=None, size=10):
    """
    generate a bitmap for a character from a font

    :param str char: character to generate
    :param str typeface: typeface to use
    :param int size: size to draw
    :return: base64 encoded bitmap of a character
    :rtype: str
    """
    font = ImageFont.truetype(typeface, size)
    bitmap = font.getmask(char, mode='L')
    bitmap = bytes(bitmap)
    return base64.b64encode(bitmap)

def find(typeface, size=10, n_cores=4):
    """
    find all homoglyphs in a font

    :param str typeface: filepath to a font file
    :param int size: size of characters to draw
    :param int n_cores: cores to use
    :return: unicode decimals with matching bitmaps
    :rtype: pandas series of lists
    """
    # compile bitmap() as a partial function and send to the pool
    # churn through every possible unicode point
    to_pool = partial(bitmap, typeface=typeface, size=size)
    with multiprocessing.Pool(n_cores) as pool:
        print("+ Generating bitmaps") 
        bitmaps = pool.map(to_pool, [chr(i) for i in range(0x10ffff)])

    # get the bitmap for a whitespace
    whitemap = bitmap(chr(20), typeface, size)
    # filter out bitmaps that match whitespace or that are empty
    df = pd.DataFrame(enumerate(bitmaps), columns=['DEC', 'BITMAP'])
    df = df[(df['BITMAP'] != whitemap) & (df['BITMAP']!=b'')]

    # group decimals by matching bitmaps
    print("+ Grouping character data")
    groups = (
        df
        .groupby('BITMAP')['DEC']
        .apply(list)
    )

    # remove any single bitmaps (no matches) or groups with >1000 
    # characters
    groups = groups[(1 < groups.apply(len)) & (groups.apply(len) < 1000)]
    return groups.reset_index(drop=True)

def filter_files(args):
    """
    identify files to render

    :param namespace args: command line arguments
    :return: files to render
    :rtype: list
    """
    infiles = os.listdir(args.indir)
    outfiles = os.listdir(args.outdir)
    outfiles = [f[:-5] for f in outfiles if f.startswith('.') == False]
    to_run = [f for f in infiles if f.startswith('.') == False and f[:-4] not in outfiles]
    print(len(outfiles), "fonts already generated. Generating", len(to_run), "fonts")
    return to_run

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--indir', type=str)
    parser.add_argument('--outdir', type=str)
    parser.add_argument('--ncores', type=int)
    args = parser.parse_args()

    fnames = filter_files(args)

    for f in fnames:
        name = f[:-4]
        print("Finding homoglyphs for", name)
        path = os.path.join(args.indir, f)
        groups = find(path, size=100, n_cores=args.ncores)
        outpath = os.path.join(args.outdir, name + '.json')
        groups.to_json(outpath)
