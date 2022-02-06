#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import os
from homoglypher.process_data import FontTable
import pandas as pd
import numpy as np

def compile_data(file_list, indir):
    """
    sum every co-occurrence table in a directory

    :param list file_list: list of tables
    :param str indir: name of the input directory
    :return: metadata for the fonts, summed co-occurrence table
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
    """
    reformat the co-occurrence table to maintain proper order

    :param pandas dataframe coocc: summed co-occurrence table
    :return: reformatted co-occurrence table
    :rtype: pandas dataframe
    """
    reorder = [str(c) for c in coocc.index]
    coocc = coocc.reindex(columns=reorder)
    coocc.columns = coocc.columns.astype(int)
    coocc = coocc.fillna(0)
    return coocc

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--indir', type=str)
    parser.add_argument('--outdir', type=str)
    args = parser.parse_args()

    fnames = os.listdir(args.indir)

    records, coocc = compile_data(fnames, args.indir)
    coocc = reformat_coocc(coocc)

    records.to_csv(os.path.join(args.outdir, "metadata.csv"))
    coocc.to_csv(os.path.join(args.outdir, "font_coocc.csv"))
