#!/usr/local/bin/python
import multiprocessing
import os
import subprocess

def run(num):
    print ("test0 " + str(num))
    subprocess.call('hostname', shell=True)

def main():
    pool = multiprocessing.Pool()
    for i in range(5):
        pool.apply_async(run, args=(i, ))
    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
