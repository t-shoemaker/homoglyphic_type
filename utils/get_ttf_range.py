#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import glob
import re
import subprocess
from collections import Counter
import pandas as pd

def get_range(ttf):
    """use the formatted output of `fc-query` to find the character range of a ttf.

    :param ttf: path to a ttf file
    :type ttf: str
    :returns: a block of whitespace-separated hex ranges
    :rtype: str
    """ 
    to_run = ["fc-query", "--format='%{charset}\n'", ttf]
    result = subprocess.run(to_run, stdout=subprocess.PIPE)
    stdout = result.stdout.decode('ascii')
    # some files have multiple styles stored inside them. we take the first
    stdout = stdout.split("\n")
    return ''.join(stdout[0])

def expand_range(r):
    """expand the hex ranges to include every decimal therein.

    :param r: a hex range from a ttf
    :type r: str
    :returns: every decimal within a range
    :rtype: list
    """
    # split on whitespace
    r = [i for i in r.split()]
    # remove stray apostrophes
    r = [re.sub("\'", "", i) for i in r]

    # build a buffer for the range, convert start and end to integers, get decimals
    whole_range = []
    for i in r:
        i = i.split("-")
        if len(i) > 1:
            start, end = int(i[0], 16), int(i[1], 16)
            for j in list(range(start, end)):
                whole_range.append(j)
        elif i != ['']:
            i = int(i[0], 16)
            whole_range.append(i)
        else:
            continue

    return whole_range

def main(args):
    """collect paths to ttf files, get their ranges, and return a compiled listing.

    :param args: command line arguments
    :type args: namespace arguments
    """
    # set up a counter and get the files, then expand the ranges
    c = Counter()
    paths = glob.glob(args.indir + "/*.ttf")
    for ttf in paths:
        r = get_range(ttf)
        expanded = expand_range(r)
        c.update(expanded)

    # format into a dataframe
    df = pd.DataFrame.from_dict(c, orient='index', columns=['COUNT'])
    df = (
        df
        .sort_index()
        .reset_index()
        .rename(columns={'index': 'DEC'})
    )
    # and save
    df.to_csv(args.outfile)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '--indir',
        type=str
    )
    parser.add_argument(
        '--outfile',
        type=str
    )
    args = parser.parse_args()
    main(args)
