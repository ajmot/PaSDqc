#!/usr/bin/env python

# MDAqc.py - top level executible for MDAqc package
#
# v 0.0.6
# rev 2017-03-18 (MS: Added documentation)
# Notes:

import os
import argparse
import pathlib2
import multiprocessing as mp

from src import mappable_positions
from src import PSDTools
from src import extra_tools

def extract(args):
    """ Extract coverage at uniquely mappable positions in a bam file
    """
    out_dir = os.path.join(args.out_dir, 'tmp')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if args.file_list:
        with open(args.file_list, 'r') as f:
            args.in_file = [line.rstrip('\n') for line in f]

        f.close()

    chrom_list = extra_tools.chroms_from_build(args.build)

    pool = mp.Pool(processes=args.n_procs)

    for f_in in args.in_file:
        # print(f_in)
        pool.apply_async(mappable_positions.extract_coverage, args=(f_in, out_dir, chrom_list), kwds={'build':args.build, 'map_qual':args.map_qual})

    pool.close()
    pool.join()

def PSD(args):
    """ Calculate power spectral densities from a directory of coverage files
    """
    dir_in = pathlib2.Path(args.dir_in)
    dir_search = dir_in / 'tmp'

    pattern = "*.cov"
    if args.pattern:
        pattern = '*' + args.pattern + pattern

    f_list = sorted(dir_search.glob(pattern))
    samples = [f.name.split('.chr')[0] for f in f_list]
    samples = set(samples)
    print(samples)

    pool = mp.Pool(processes=args.n_procs)

    for sample in samples:
        # _build_and_save(dir_in, sample=sample)
        fname = sample + ".chroms.spec"
        fout = dir_in / fname

        p = pool.apply_async(_build_and_save, (dir_search, sample, fout))
        # p.get()
        # pool.apply_async(_build_and_save, args=(dir_in), kwds={'sample': sample})

    pool.close()
    pool.join()

def _build_and_save(dir_in, sample, fout):
    """ Wrapper to build and save SamplePSD objects
    """

    psd = PSDTools.SamplePSD.build_from_dir(str(dir_in), sample=sample)
    psd.save(str(fout))

def parse_args():
    parser = {}
    parser['argparse'] = argparse.ArgumentParser(description='MDAqc: tools for MDA quality control checks')
    parser['subparse'] = parser['argparse'].add_subparsers()

    parser['extract'] = parser['subparse'].add_parser('extract', help='Extract depth at uniquely mappable positions from bam file(s)')
    parser['extract'].add_argument('-i', '--in_file', default=None, nargs='+', help='input bam file(s)')
    parser['extract'].add_argument('-f', '--file_list', default=None, help='file of bam paths to use instead of -i')
    parser['extract'].add_argument('-o', '--out_dir', default='.', help='output directory')
    parser['extract'].add_argument('-n', '--n_procs', default=1, type=int, help='number of cores to use')
    parser['extract'].add_argument('-b', '--build', default='grch37', help='genome build')
    parser['extract'].add_argument('-q', '--map_qual', default=30, help='mapping quality threshold')
    parser['extract'].set_defaults(func=extract)

    parser['PSD'] = parser['subparse'].add_parser('PSD', help='Estimate power spectral densities from coverage files')
    parser['PSD'].add_argument('-d', '--dir_in', default=None, help='directory in which to search for coverage files')
    parser['PSD'].add_argument('-n', '--n_procs', default=1, type=int, help='number of cores to use')
    parser['PSD'].add_argument('-p', '--pattern', default=None, help='pattern to match when finding samples')
    parser['PSD'].set_defaults(func=PSD)

    return parser['argparse'].parse_args()

if __name__ == "__main__":
    args = parse_args()
    args.func(args)
