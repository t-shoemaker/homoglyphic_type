#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import dask.dataframe as dd
import pandas as pd
import os

def stack_frames():
    """transform a directory of co-occurrence tables into adjacency pairs."""
    files = [f for f in os.listdir(indir) if f.startswith('.') == False]

    count = 0
    for f in files:
        print(f"Loading {f}")
        path = os.path.join(indir, f)
        df = pd.read_csv(path, index_col=0)
        df = (
            df
            .stack()
            .to_frame()
            .reset_index()
            .rename(columns={'level_0': 'DEC', 'level_1': 'PAIR', 0: 'COUNT'})
        )
        outpath = os.path.join(outdir, f)
        df.to_csv(outpath)
        count += 1
        if count % 25 == 0:
            print(f"+ Stacked {count} of {len(files)}")

def add_frames():
    """stream in the adjacency pairs with dask and count duplicates."""
    path = outdir + "/*.csv"
    df = dd.read_csv(path).set_index('Unnamed: 0')
    df = (
        df
        .groupby(['DEC', 'PAIR'])['COUNT']
        .sum()
    )
    df.compute()

    return df

def main(args):
    """collect directory info to send to the stacking and adding functions.

    :param args: command line arguments
    :type args: namespace arguments
    """
    global indir, outdir
    indir = args.indir
    outdir = args.outdir 

    print("Stacking frames")
    stack_frames()

    print("Adding frames")
    df = add_frames()
    df = df.reset_index()
    df.to_csv(args.outfile, single_file=True)

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
        '--outfile',
        type=str
    )
    args = parser.parse_args()
    main(args)
