import multiprocessing
import os
import subprocess
import sys
import threading
import time

import glbl as g 

from glob import glob

lock = multiprocessing.Lock()

def run_and_check((tc_name, prj_name)):
    args = g.get_value('args')
    toplog_dir = os.path.join(prj_name, 'log')
    if not os.path.exists(toplog_dir):
        os.makedirs(toplog_dir)
    print "checking for " + os.path.split(prj_name)[-1]
    ret = subprocess.call('%s -e \$bkc_num=%s -e \$toplog_dir=%s -e \$semi_auto=TRUE -no-gui %s > /dev/null' % (os.path.join(prj_name, 'simics'), args.bkc_num, toplog_dir, tc_name), shell=True) 
    result = 'pass' if ret == 11 else 'fail'

    lock.acquire()
    simics_result_dict = g.get_value('simics_result_dict')
    print simics_result_dict
    simics_result_dict[tc_name][os.path.split(prj_name)[-1]] = result
    g.set_value('simics_result_dict', simics_result_dict)
    print g.get_value('simics_result_dict')
    lock.release()

    print os.path.split(prj_name)[-1] + " ending with " + result 

def init_lock(l):
    global lock
    lock = l
    
def run_top(tc_name):
    global lock
    args = g.get_value('args')
    simics_prj_folder_dict = g.get_value('simics_prj_folder_dict')
    tc_name_list = []
    for i in range(7):
        tc_name_list.append(tc_name)
    # simics_result_dict = g.get_value('simics_result_dict')
    # simics_result_dict[tc_name] = {}
    # g.set_value('simics_result_dict', simics_result_dict)
    pool = multiprocessing.Pool(processes=7, initializer=init_lock, initargs=(lock,))              
    pool.map(run_and_check, zip(tc_name_list, simics_prj_folder_dict[tc_name].values()), chunksize=1)
    # check simics_result_dict
    simics_result_dict = g.get_value('simics_result_dict')
    print simics_result_dict
    pass_list = []
    for key in simics_result_dict[tc_name].keys():
        if simics_result_dict[tc_name][key] == 'pass':
            pass_list.append(key)
    return pass_list

def packages_cmp(x, y):
    if len(x) == len(y):
        if x < y: return -1
        elif x == y: return 0
        else: return 1
    elif len(x) < len(y): return -1
    else: return 1
    
def get_all_simics_packages():
    falconvalley_list = glob(r'/localdisk/bkc/debug/simics/*falconvalley*')
    lbg_wb_pmc_list = glob(r'/localdisk/bkc/debug/simics/*lbg_wb_pmc*')
    whitley_list= glob(r'/localdisk/bkc/debug/simics/*whitley*')
    g.set_value('falconvalley_list', falconvalley_list.sort(cmp=packages_cmp))
    g.set_value('lbg_wb_pmc_list', lbg_wb_pmc_list.sort(cmp=packages_cmp))
    g.set_value('whitley_list', whitley_list.sort(cmp=packages_cmp))

def create_new_prj(simics_checking_dir, package_setup_list):
    args = g.get_value('args')
    prj_setup_cmd = g.get_value('prj_setup_cmd')
    if not os.path.exists(simics_checking_dir):
        print simics_checking_dir + ' doesnt exist. Creating directory'
        os.makedirs(simics_checking_dir)
    # print prj_setup_cmd[:-1] + ' ' + simics_checking_dir
    # os.system(prj_setup_cmd[:-1] + ' ' + simics_checking_dir + ' --ignore-existing-files')
    os.system(prj_setup_cmd[:-1] + ' ' + simics_checking_dir)
    os.system('cp -r ' + os.path.join(args.tos_dir, '*') + ' ' + simics_checking_dir)
    package_list_fobj = open(os.path.join(simics_checking_dir, '.package-list'), 'w+')
    for item in package_setup_list:
        package_list_fobj.writelines(item)
        package_list_fobj.write('\n')
    package_list_fobj.close()

def generate_permutations(tc_name):
    args = g.get_value('args')
    permutation_list = g.get_value('permutation_list')
    simics_dict = g.get_value('simics_dict')
    simics_prj_folder_dict = g.get_value('simics_prj_folder_dict')
    simics_prj_folder_dict[tc_name] = {}
    simics_checking_superior_dir = os.path.join(args.prj_dir, 'dbg', 'ad_simics_checking', os.path.split(tc_name)[-1])
    for package_item in permutation_list:
        package_setup_dict = simics_dict['default'].copy()
        package_setup_dict.update(simics_dict[g.get_value('curr_bkc_num')].items())
        for item in package_item:
            package_setup_dict[item] = simics_dict[g.get_value('prev_bkc_num')][item]
        simics_checking_dir = os.path.join(simics_checking_superior_dir, '_'.join(package_item))
        create_new_prj(simics_checking_dir, package_setup_dict.values())
        simics_prj_folder_dict[tc_name]['_'.join(package_item)] = simics_checking_dir
    g.set_value('simics_prj_folder_dict', simics_prj_folder_dict)

def get_simics_three(simics_dir_list):
    falconvalley = ''
    lbg_wb_pmc = ''
    whitley = ''
    for item in simics_dir_list:
        if 'falconvalley' in item:
            falconvalley = item
        elif 'lbg_wb_pmc' in item:
            lbg_wb_pmc = item
        elif 'whitley' in item:
            whitley = item
    return (falconvalley, lbg_wb_pmc, whitley)

def get_simics_default_package(simics_dir_list):
    eclipse = ''
    eclipse_uefi = ''
    testcards = ''
    for item in simics_dir_list:
        if 'eclipse' in item and 'eclipse-uefi' not in item:
            eclipse = item
        elif 'eclipse-uefi' in item:
            eclipse_uefi = item
        elif 'testcards' in item:
            testcards = item
    return (eclipse, eclipse_uefi, testcards)

# pp stands for pass package
def auto_narrow_down_simics(tc_name, pass_package, topworking_dir, pp_start_index, pp_end_index, pp_start_version, pp_end_version):
    global lock
    # print "auto narrow down simics"
    print pass_package + " starting_at " + str(pp_start_index) + " with version " + os.path.split(pp_start_version)[-1]
    print pass_package + " ending_at " + str(pp_end_index) + " with version " + os.path.split(pp_end_version)[-1]
    if pp_end_index <= pp.start_index:
        print "Something went wrong with the previous " + pass_package + " version. Please check the log file and try manually."
        g._exit()
    if pp_end_index == pp_start_index + 1:
        print_log = tc_name + ' FAILED AT ' + pass_package + ' V. ' + os.path.split(pp_end_version)[-1]
        ret = os.system('echo "' + print_log + '" | tee ' + os.path.join(topworking_dir, 'final_msg.txt'))
        return 

    args = g.get_value('args')
    pass_package_list = g.get_value(pass_package + '_list')
    package_setup_dict = simics_dict['default'].copy()
    package_setup_dict.update(simics_dict[g.get_value('curr_bkc_num')].items())
    run_num = min(args.ad_num, pp_end_index - pp_start_index - 1)
    gap = (pp_end_index - pp_start_index - 1) / run_num

    tmp_prj_list = []
    tc_name_list = []
    for i in range(run_num):
        tc_name_list.append(tc_name)
    for item in pass_package_list[pp_start_index + 1, pp_end_index, gap]:
        # package_setup_dict[pass_package] = os.path.join('/localdisk/bkc/debug/simics/', item)
        package_setup_dict[pass_package] = item
        tmp_prj_list.append(os.path.join(topworking_dir, item))
        create_new_prj(os.path.join(topworking_dir, item), package_setup_dict.values())
        
    simics_result_dict = g.get_value('simics_result_dict')
    simics_result_dict[tc_name] = {}
    g.set_value('simics_result_dict', simics_result_dict)
    pool = multiprocessing.Pool(processes=run_num, initializer=init_lock, initargs=(lock,))              
    pool.map(run_and_check, zip(tc_name_list, tmp_prj_list), chunksize=1)
    
    simics_result_dict = g.get_value('simics_result_dict')
    pp_nxt_start_index = pp_start_index
    pp_nxt_end_index = pp_end_index
    pp_nxt_start_version = pp_start_version
    pp_nxt_end_version = pp_end_version
    for item in simics_result_dict[tc_name].keys():
        if simics_result_dict[tc_name][item] == 'pass':
            pp_nxt_start_index = max(pp_nxt_start_index, pass_package_list.index(item))
            pp_nxt_start_version = item
        elif simics_result_dict[tc_name][item] == 'fail':
            pp_nxt_end_index = min(pp_nxt_end_index, pass_package_list.index(item))
            pp_nxt_end_version = item
    auto_narrow_down_simics(tc_name, pass_package, topworking_dir, pp_nxt_start_index, pp_nxt_end_index, pp_nxt_start_version, pp_nxt_end_version)
    return 

def auto_narrow_down(tc_name):
    get_all_simics_packages()
    args = g.get_value('args')
    bkc_num_dir = g.get_value('bkc_num_dir')
    curr_bkc_num = g.get_value('curr_bkc_num')
    prev_bkc_num = g.get_value('prev_bkc_num')
    simics_result_dict = g.get_value('simics_result_dict')
    simics_result_dict[tc_name] = {}
    g.set_value('simics_result_dict', simics_result_dict)

    # get project-setup command
    process = os.popen('find ' + os.path.join(bkc_num_dir, curr_bkc_num)+ ' -name project-setup')
    prj_setup_cmd = process.read()
    process.close()

    # os.system(os.path.join(args.prj_dir, 'bin/addon-manager' + "-b -C")
    curr_simics_package_list = [os.path.join(bkc_num_dir, curr_bkc_num, 'simics', item) for item in os.listdir(os.path.join(bkc_num_dir, curr_bkc_num, 'simics'))]
    prev_simics_package_list = [os.path.join(bkc_num_dir, prev_bkc_num, 'simics', item) for item in os.listdir(os.path.join(bkc_num_dir, prev_bkc_num, 'simics'))]
    curr_simics_three_list = get_simics_three(curr_simics_package_list)
    prev_simics_three_list = get_simics_three(prev_simics_package_list)
    simics_default_package_list = get_simics_default_package(curr_simics_package_list)

    simics_dict = {}
    simics_dict[curr_bkc_num] = {'falconvalley':curr_simics_three_list[0], 'lbg_wb_pmc':curr_simics_three_list[1], 'whitley':curr_simics_three_list[2]}
    simics_dict[prev_bkc_num] = {'falconvalley':prev_simics_three_list[0], 'lbg_wb_pmc':prev_simics_three_list[1], 'whitley':prev_simics_three_list[2]}
    simics_dict['default'] = {'eclipse':simics_default_package_list[0], 'eclipse_uefi':simics_default_package_list[1], 'testcards':simics_default_package_list[2]}

    g.set_value('simics_dict', simics_dict)
    g.set_value('prj_setup_cmd', prj_setup_cmd)

    # test for last simics package
    generate_permutations(tc_name)
    pass_list = run_top(tc_name)
    tmp_cnt = 0 
    pass_package = None
    for item in pass_list:
        if item == 'falconvalley': 
            tmp_cnt = tmp_cnt + 1
            pass_package = 'falconvalley'
        elif item == 'lbg_wb_pmc': 
            tmp_cnt = tmp_cnt + 1
            pass_package = 'lbg_wb_pmc'
        elif item == 'whitley': 
            tmp_cnt = tmp_cnt + 1
            pass_package = 'whitley'
    print "all passed package combinations with previous verions is shown bellow:"
    if len(pass_list) == 0:
        print "no package passed"
        # TODO
        print "forwarding to check ... "
    else:
        for item in pass_list:
            print item
        if tmp_cnt == 1:
            print pass_package + " is considered having the most possibility of failure"
            # auto_narrow_down_simics()
            pass_package_list = g.get_value(pass_package + '_list')
            curr_pass_package_index = pass_package_list.index(simics_dict[curr_bkc_num][pass_package])
            prev_pass_package_index = pass_package_list.index(simics_dict[prev_bkc_num][pass_package])
            curr_pass_package_version = simics_dict[curr_bkc_num][pass_package]
            prev_pass_package_version = simics_dict[prev_bkc_num][pass_package]

            topworking_dir = os.path.join(args.prj_dir, 'dbg/ad_simics_checking', os.path.split(tc_name)[-1], pass_package, 'simics_dbg')
            for i in range(args.ad_num):
                os.system(prj_setup_cmd[:-1] + ' ' + os.path.join(topworking_dir, 'dbg_', i))
            auto_narrow_down_simics(tc_name, pass_package, topworking_dir, prev_pass_package_index, curr_pass_package_index,prev_pass_package_version, curr_pass_package_version)
        else:
            print "more than one single package with previous version passed. Please check manually"
