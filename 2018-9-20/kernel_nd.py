import os
import argparse
import multiprocessing
import subprocess
from myp import *

kernel_lib_dir = '/localdisk/bkc/debug/intel_next/daily'
kernel_lib_file = os.path.join(kernel_lib_dir, 'org.txt')
prj_dir = os.path.join((os.getcwd()).split('/')[:-4])

def args_init():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('kernel_start', help='specify the first kernel directory name in org.txt, ex. 2018-09-07')
    parser.add_argument('kernel_end', help='specify the last kernel directory name in org.txt, ex. 2018-09-07')
    parser.add_argument('--process-num', '-p', default='13', help='specify the maximum process that run parallel')
    args = parser.parse_args()

def get_kernel_list():
    tmp_list = os.listdir(kernel_lib_dir)
    for i in range(len(tmp_list)):
        if args.kernel_start in tmp_list[i]:
            spos = i
            break
    for i in range(len(tmp_list)):
        if args.kernel_end in tmp_list[i]:
            epos = i
    return [os.path.join(kernel_lib_dir, item) for item in
            tmp_list[spos:min(epos + 1, len(tmp_list))]]

class CraffNd(Target):
    def __init__(self, pos, kernel, tc_name):
        super(CraffNd, self).__init__(pos)
        self.kernel = kernel
        self.__tc_name = tc_name
        self.diff_craff = None

    def get_diff_craff(self):
        command = os.path.join(prj_dir, 'simics') + \
                  ' -e \$local_linux_kernel=' + self.kernel + \
                  ' -e \$semi_auto=TRUE ' + \
                  os.path.join(prj_dir, 'dbg/triage/kernel/update_kernel.simics')
        quit_code = subprocess.call(command, shell=True)
        for item in os.listdir(prj_dir):
            if item[-6:] == '.craff' and item[-6:] in local_linux_kernel:
                return os.path.join(prj_dir, item)

    def run(self):
        self.diff_craff = self.get_diff_craff()
        toplog_dir = os.path.join(prj_dir, 'log', '00')
        if not os.path.exists(toplog_dir):
            os.makedirs(toplog_dir)
        command = os.path.join(prj_dir, 'simics') + \
                  "-e \$toplog_dir=" + toplog_dir + \
                  "-e \$semi_auto=TRUE " + self.__tc_name
        return subprocess.call(command, shell=True)

    def judge(self, return_code):
        return True if quit_code == 11 else False

if __name__ == '__main__':
    args_init()
    kernel_list = get_kernel_list()
    kernel_list.sort()
    craff_nd_list = []
    for i in range(len(kernel_list)):
        craff_nd_list.append(CraffNd(i, kernel_list[i], args.tc_name))

    fail_point = NarrowDown(args.process_num, craff_nd_list).narrow_down()
    if fail_point == len(diff_craff_list):
        print "all pass"
    else:
        print "fail at " + craff_nd_list[fail_point].kernel
