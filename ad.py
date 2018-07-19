#!/usr/bin/python

import argparse
import datetime
# import multiprocessing
# import operator
import os
# import os.path
import re
import sys
import time

import glbl as g
import adbios
from glob import glob
# import adsimics

def get_bin(file_list):
    ret_list = []
    for item in file_list:
        if item[-4:] == '.bin':
            ret_list.append(item)
    return ret_list

def get_bios_index(bios_version, bios_list):
    # tmp = bios_version.split('.')
    time_stamp = ''
    time_stamp_p = re.compile(r'(?<=WLYDCRB\.86B\.BR\.)(.*)(?=_LBG_SPS.*)')
    match = time_stamp_p.search(bios_version)
    assert match, 'standard format of the name of released bios might have been changed.'
    time_stamp = match.group()
    # time_stamp = '.'.join(tmp[4:8]) + '.' + tmp[8][:-8]
    ret_index = 0
    for item in bios_list:
        if time_stamp in item:
            return (ret_index, item)
        ret_index = ret_index + 1
    # TODO: assert. Check if make it right 
    assert ret_index < len(bios_list), bios_version + ' not found in the original bios directory.'

def args_init():
    parser = argparse.ArgumentParser()
    # add arguments
    # TODO: add more arguments. Check if make it right.
    # TODO: add auto narrow down parallel exec num
    # subparsers = parser.add_subparsers(dest='subparser_name', help='sub-command help')
    # parser_run = subparsers.add_parser('run', help='TODO', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser_run.add_argument('-p', '--process-num', type=int, choices=range(1, 13), default=3, help = "specify the parallel execution number of simics testcases")
    # parser_run.add_argument('tc_name', help='specify one simics testcase')
    # parser_run.add_argument('-a', '--ad-num', type=int, choices=range(1, 13), default=3, help = "TODO")

    # TODO: 
    # parser_run.add_argument('-d', '--prj-dir', default='../', help='simics project directory')
    # parser_run.add_argument('-b', '--bkc-num', help='specify bios version using work week directory name in the main bios version directory. Example: --bkc_num 18ww26. Default will be the relative path of current project directory')
    parser.add_argument('tc_name', help='specify the simics testcase')
    parser.add_argument('-a', '--ad-num', type=int, choices=range(1, 13), default=3, help = "specify the number of parallel running testcases")
    parser.add_argument('-d', '--prj-dir', default='../', help='specify simics project directory')
    parser.add_argument('-b', '--bkc-num', default=os.path.split(os.path.split(os.getcwd())[0])[-1], help='specify bios version using bkc number. [Example: -b 18ww26]. Default will be the relative path of current project directory')
    parser.add_argument('-s', '--semi-auto', action="store_true", help='use this argument when running semi-auto testcase')
    parser.add_argument('-e', '--simics-args', default=None, help='specify the arguments pass to simics')
    parser.add_argument('-t', '--run-together', action="store_true", help='run all at the same time')
    args = parser.parse_args()
    args.prj_dir = os.path.abspath(args.prj_dir)
    args.tc_name = os.path.abspath(args.tc_name)
    assert os.path.exists(args.prj_dir), args.prj_dir + " doesn't exist"
    assert os.path.exists(args.tc_name), args.tc_name + " doesn't exist"
    return args

def set_global_value():
    g._init()
    # bios relative directory declaration
    bkc_num_dir = '/localdisk/bkc/icx'
    bios_lib_dir = '/localdisk/bkc/debug/icx_bios/daily'
    bios_list = get_bin(os.listdir(bios_lib_dir)) 
    bios_list.sort()
    # set script starting time
    start_time = time.strftime('%y%m%d_%H%M%S_%a')
    # set script log directory
    ad_logdir = '%s/ad_%s' % (os.path.join(args.prj_dir, 'log'), start_time)
    bkc_num_list = os.listdir(bkc_num_dir)
    bkc_num_list.sort()
    curr_bkc_num = args.bkc_num
    # if args.bkc_num == None:
    #     curr_bkc_num = os.path.split(args.prj_dir)[-1]
    # else:
    #     curr_bkc_num = args.bios
    # assuming that current workweek is not the first directory
    # TODO: Q: fix?
    prev_bkc_num = bkc_num_list[bkc_num_list.index(curr_bkc_num) - 1]
    # get bios filename of current and previous bkc release 
    # curr_bios = os.listdir(os.path.join(bkc_num_dir, curr_bkc_num, 'build/BIOS'))[0]
    # prev_bios = os.listdir(os.path.join(bkc_num_dir, prev_bkc_num, 'build/BIOS'))[0]
    curr_bios = glob(os.path.join(bkc_num_dir, curr_bkc_num, 'build/BIOS', '*bin'))[0]
    prev_bios = glob(os.path.join(bkc_num_dir, prev_bkc_num, 'build/BIOS', '*bin'))[0]


    (curr_bios_index, curr_bios_version) = get_bios_index(curr_bios, bios_list)
    (prev_bios_index, prev_bios_version) = get_bios_index(prev_bios, bios_list)
    if args.run_together:
        prev_bios_index = prev_bios_index - 1
        prev_bios_version = bios_list[prev_bios_index]
    # simics relative direcotry declaration
    binary_dir = os.path.join(args.prj_dir, 'bin')
    # simics debuging 
    permutation_list = [['falconvalley'], ['lbg_wb_pmc'], ['whitley'], ['falconvalley', 'lbg_wb_pmc'], ['falconvalley', 'whitley'], ['lbg_wb_pmc', 'whitley'], ['falconvalley', 'lbg_wb_pmc', 'whitley']]
    g.set_value('args', args)
    g.set_value('bkc_num_dir', bkc_num_dir)
    g.set_value('bios_lib_dir', bios_lib_dir)
    g.set_value('bios_list', bios_list)
    g.set_value('start_time', start_time)
    g.set_value('ad_logdir', ad_logdir)
    g.set_value('bkc_num_list', bkc_num_list)
    g.set_value('curr_bkc_num', curr_bkc_num)
    g.set_value('prev_bkc_num', prev_bkc_num)
    g.set_value('curr_bios', curr_bios)
    g.set_value('prev_bios', prev_bios)
    g.set_value('prev_bios_index', prev_bios_index)
    g.set_value('prev_bios_version', prev_bios_version)
    g.set_value('curr_bios_index', curr_bios_index)
    g.set_value('curr_bios_version', curr_bios_version)
    g.set_value('binary_dir', binary_dir)
    g.set_value('project_num', 0)
    g.set_value('permutation_list', permutation_list)

if __name__ == '__main__':
    args = args_init()
    set_global_value()
    print "current working project: " + args.prj_dir
    print "current bkc number: " + g.get_value('curr_bkc_num')
    if args.tc_name:
        # firstly check previous version
        if args.run_together:
            adbios.auto_narrow_down_bios(args.tc_name, g.get_value('prev_bios_index'), g.get_value('curr_bios_index'), g.get_value('prev_bios_version'), g.get_value('curr_bios_version'))
        else:
            if not adbios.run_and_check((args.tc_name, g.get_value('prev_bios_version'))):
                print "NOTE: Testcase failed with last released BIOS. probably not caused by BIOS. "
                print "preparing to checking all Simics version between " + g.get_value('prev_bios_version')  + " and " + g.get_value('curr_bios_version')
                # TODO not now
                # adsimics.auto_narrow_down_simics()
            else:
                print "NOTE: Testcase passed with last released BIOS."
                print "preparing to check all BIOS version between " + g.get_value('prev_bios_version') + " and " + g.get_value('curr_bios_version')
                adbios.auto_narrow_down_bios(args.tc_name, g.get_value('prev_bios_index'), g.get_value('curr_bios_index'), g.get_value('prev_bios_version'), g.get_value('curr_bios_version'))
    else:
        # TODO
        pass
    g._exit()
