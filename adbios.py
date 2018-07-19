import csv
import multiprocessing
import os
import operator
import sys

import glbl as g

# def TODO_func():
def check_passed(csv_result):
    csv_file = open(csv_result)
    csv_reader = csv.reader(csv_file)
    csv_data = list(csv_reader)
    csv_file.close()
    if csv_data[1][1] == '10' or csv_data[1][2] == 'fail':
        return False
    # print "csv column 1 " + csv_data[1][1]
    # print "csv column 1 " + csv_data[1][2]
    return True

def run_tc(tc_name, bios_version, ad_result):
    args = g.get_value('args')
    ad_logdir = g.get_value('ad_logdir')
    bios_lib_dir = g.get_value('bios_lib_dir')
    print "starting .. " + tc_name + " with bios " + bios_version
    tmp_cmd = '%s -e \$bios=%s -e \$csv_file_name=%s -e \$toplog_dir=%s -e \$semi_auto=TRUE' % (os.path.join(g.get_value('args').prj_dir, 'simics'), os.path.join(bios_lib_dir, bios_version), ad_result, os.path.join(ad_logdir, bios_version))
    if args.simics_args:
        tmp_cmd = tmp_cmd + " -e '" + args.simics_args + "'"
    tmp_cmd = tmp_cmd + ' -no-gui %s > /dev/null' % tc_name
    ret = os.system('%s -e \$bios=%s -e \$csv_file_name=%s -e \$toplog_dir=%s -e \$semi_auto=TRUE -no-gui %s > /dev/null' % (os.path.join(g.get_value('args').prj_dir, 'simics'), os.path.join(bios_lib_dir, bios_version), ad_result, os.path.join(ad_logdir, bios_version), tc_name))
    if args.semi_auto:
        result = None
        while True:
            result = raw_input('Please give the result of BIOS V. ' + bios_version + ' [p/f][pass/fail]')
            if result == 'pass' or result == 'fail' or result == 'p' or result == 'f': break
        result_fobj = open(ad_result, 'r')
        result_line = result_fobj.readlines()
        result_fobj.close()
        result_words = result_line[1].split(',')
        print result_line
        print result_words
        result_words[1], result_words[2] = ('11', 'pass') if result == 'pass' or result == 'p' else ('', 'fail')
        result_line[1] = ','.join(result_words)
        result_fobj = open(ad_result, 'w')
        for line in result_line:
            result_fobj.write(line)
        result_fobj.close()

        
    # TODO: X window exception might raise 
    print "ending .. " + tc_name + " with bios " + bios_version

def run_and_check((tc_name, bios_version)):
    ad_logdir = g.get_value('ad_logdir')
    ad_result = '%s/bios_version-%s.csv' % (ad_logdir, '.'.join(bios_version.split('.')[:-1])) 
    run_tc(tc_name, bios_version, ad_result)

    is_pass = check_passed(ad_result)
    print "test case " + ('passed' if is_pass else 'failed') + " with BIOS V. " + bios_version
    check_result_fobj = open(os.path.join(ad_logdir, os.path.split(tc_name)[-1] + '.csv'), 'a+')
    csv_writer = csv.writer(check_result_fobj)
    result_list = [tc_name, bios_version, 'pass' if is_pass else 'fail']
    csv_writer.writerow(result_list)
    check_result_fobj.close()
    return is_pass

def auto_narrow_down_bios(tc_name, bios_start_index, bios_end_index, bios_start_version, bios_end_version):
    ad_logdir = g.get_value('ad_logdir')
    bios_list = g.get_value('bios_list')

    print "bios starting at " + str(bios_start_index) + " with version " + bios_start_version
    print "bios ending   at " + str(bios_end_index) + " with version " + bios_end_version
    if bios_end_index <= bios_start_index:
        print "Something went wrong with the previous BIOS version. Please check the log file and try manually."
        # TODO: optimize the following line
        g._exit()
    if bios_end_index == bios_start_index + 1:
        # found 
        print_log = tc_name + ' FAILED AT BIOS V. ' + bios_end_version
        ret = os.system('echo "' + print_log + '" | tee ' + os.path.join(ad_logdir, 'final_msg.txt'))
        return 
    bios_num = bios_end_index - bios_start_index - 1
    run_num = min(g.get_value('args').ad_num, bios_num)
    gap = bios_num / run_num
    tc_name_list = []
    for i in range(run_num): 
        tc_name_list.append(tc_name)
    bios_sub_list = []
    for i in bios_list[bios_start_index + 1: bios_end_index: gap]:
        bios_sub_list.append(i) 
    pool = multiprocessing.Pool(processes=run_num)              
    pool.map(run_and_check, zip(tc_name_list, bios_sub_list), chunksize=1)
    # check log
    check_result_fobj = open(os.path.join(ad_logdir, os.path.split(tc_name)[-1] + '.csv'), 'r')
    csv_reader = csv.reader(check_result_fobj)
    sorted_list = sorted(csv_reader, key=operator.itemgetter(1), reverse=True)
    check_result_fobj.close()
    bios_nxt_start_version = bios_start_version
    bios_nxt_end_version = bios_end_version

    # print sorted_list
    for item in sorted_list:
        if item[2] == 'pass':
            bios_nxt_start_version = max(item[1], bios_nxt_start_version)
        else:
            bios_nxt_end_version = min(item[1], bios_nxt_end_version)
    auto_narrow_down_bios(tc_name, bios_list.index(bios_nxt_start_version), bios_list.index(bios_nxt_end_version), bios_nxt_start_version, bios_nxt_end_version)
    return
