#!/usr/bin/python2.7
import multiprocessing
import os
import subprocess

def run(num):
    print ("test1 " + str(num))

def main():
    pool = multiprocessing.Pool()
    for i in range(5):
        pool.apply_async(run, args=(i, ))
    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
