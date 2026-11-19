# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 16:16:58 2024

@author: joPHOBEA

This script either initialises the ERMESS RESEARCH algorithm to creates initial population OR runs the ERMESS PRO algorithm

It :
1. Loads input data from an Excel configuration file
2. Builds the optimization environment
3. Runs the optimization model

The algorithm relies on a hierarchical initialization strategy
and parallel evolutionary computation.

Modules used:
    - data.data_classes
    - data.read_excel
    - utils.constraints
    - evolutionnary_core
    - cost.ERMESS_cost_functions
    - reporting.write_excel

"""

import argparse
import os
import sys
import numpy as np
from multiprocessing import freeze_support
import warnings
import logging

from ERMESS_scripts.data import data_reader as Edr
from ERMESS_scripts.data import data_parsers as Edp
from ERMESS_scripts.data import data_builder as Dbl
from ERMESS_scripts.data import data_validation as Edv

from ERMESS_scripts.evolutionnary_core import ERMESS_functions_pro as Efp
from ERMESS_scripts.evolutionnary_core import ERMESS_evolutionnary_algorithm as EA

from ERMESS_scripts.reporting import post_processing as Epp

warnings.simplefilter(action='ignore', category=UserWarning)


class ERMESSInputError(Exception):
    """Raised when the input workbook cannot be loaded, validated or parsed."""


def ERMESS_pro(input_file_path=None, output_file_path=None, generations=None) :

    freeze_support()
    ##============================================================================
    # 1. INPUT DATA LOADING
    ##============================================================================

    if input_file_path is None:
        from tkinter import filedialog
        input_file_path = filedialog.askopenfilename(filetypes =[('Excel Files', '*.xlsx')], initialdir="#Specify the file path")

    try:
        data = Edr.load_excel(input_file_path)
        Edv._data_validation(data)
        structured_data = Edp._parse_ERMESSInputs(data)
    except Exception as exc:
        raise ERMESSInputError(f"{type(exc).__name__}: {exc}") from exc

    if generations is not None:
        structured_data.hyperparameterspro.n_iter = np.int64(generations)

    ##============================================================================
    # 2. ENVIRONMENT INITIALIZATION
    ##============================================================================

    Context=Dbl.build_environment(structured_data)
    if output_file_path is not None:
        Context.postprocess_config.file_name = output_file_path

    ##============================================================================
    # 3. PRO OPTIMIZATION (SIMULATING EMS DISPATCHING)
    ##============================================================================  
   
    if (Context.optimization.type_optim=='pro'):
        logging.info("Starting optimization ERMESS pro")
        Initial_population_pro = Efp.initial_population_pro(Context)           
        args_pro = (Context,Initial_population_pro)
        (Final_population,perf_ope) = EA.evolutionnary_algorithm_pro(args_pro) 
        scores=tuple(ind.fitness for ind in Final_population)
        best=Final_population[np.nanargmin(scores)]
        Epp.post_traitement(solution=best, Context=Context, datetime=structured_data.time.datetime)
    return Context.postprocess_config.file_name


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the ERMESS PRO optimisation.")
    parser.add_argument("input", nargs="?", help="input workbook (legacy positional form)")
    parser.add_argument("--input", dest="input_flag", help="input workbook (.xlsx)")
    parser.add_argument("--output", help="output workbook path (default: the workbook's Outputs sheet)")
    parser.add_argument("--generations", type=int, help="override the PRO generation count of the workbook")
    args = parser.parse_args(argv)
    input_path = args.input_flag or args.input
    if args.generations is not None and args.generations < 1:
        parser.error("--generations must be >= 1")

    try:
        output_path = ERMESS_pro(input_path, args.output, args.generations)
    except ERMESSInputError as exc:
        print(f"ERMESS_INPUT_ERROR: {exc}".replace("\n", " "), file=sys.stderr, flush=True)
        return 2
    if not output_path or not os.path.isfile(output_path):
        print(f"ERMESS: no output workbook written at {output_path}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
        