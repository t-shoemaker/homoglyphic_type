#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import os
from homoglypher.process_data import FontTable
import pandas as pd
import numpy as np

def compile_data(file_list, indir):
    """sum every co-occurrence table in a directory.

    :param file_list: list of tables
    :type file_list: list
    :param indir: name of the input directory
    :type indir: str
    :returns: metadata for the fonts, summed co-occurrence table
    :rtype: pandas dataframe
    """
    records = pd.DataFrame()
    coocc = pd.DataFrame()
    for table in file_list:
        table = FontTable(table, indir)
        records = records.append(table.record)
        coocc = coocc.add(table.coocc, fill_value=0)
    return records, coocc

def reformat_coocc(coocc):
    """reformat the co-occurrence table to maintain proper order.

    :param coocc: summed co-occurrence table
    :type cooc: pandas dataframe
    :returns: reformatted co-occurrence table
    :rtype: pandas dataframe
    """
    reorder = [str(c) for c in coocc.index]
    coocc = coocc.reindex(columns=reorder)
    coocc.columns = coocc.columns.astype(int)
    coocc = coocc.fillna(0)
    return coocc

def main(args):
    """stream in a list of co-occurrence tables and sum them.

    :param args: command line arguments
    :type args: namespace arguments
    """
    fnames = os.listdir(args.indir)

    records, coocc = compile_data(fnames, args.indir)
    coocc = reformat_coocc(coocc)

    records.to_csv(os.path.join(args.outdir), "font_metadata.csv"))
    coocc.to_csv(os.path.join(args.outdir), "fond_coocc.csv"))

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
    args = parser.parse_args()
    main(args)
