import os
import multiprocessing
import subprocess
import sys

def run(process_name, val):
    subprocess.call('python ' + process_name, shell=True)
    val.value = val.value + 1

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    val = manager.Value('myval', 0)
    pool = multiprocessing.Pool()
    cur_path = os.getcwd()
    for i in range(3):
        process_name = os.path.join(cur_path, 'test' + str(i) + '.py')
        pool.apply_async(run, args=(process_name, val))
    try:
        while val.value < 3:
            continue
    except KeyboardInterrupt:
        sys.exit()
    else:
        pool.close()
        pool.join()
