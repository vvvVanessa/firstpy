import multiprocessing
import time
from abc import ABCMeta, abstractmethod
import subprocess

def run_tc(obj):
    return obj.run_and_judge()

class Target:
    __metaclass__ = ABCMeta
    def __init__(self, pos, vis=False):
        self.__vis = vis
        self.pos = pos

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    @abstractmethod
    def judge(self, return_code):
        pass

    def visit(self):
        if self.__vis == False:
            self.__vis = True
            return False
        return True

    def run_and_judge(self):
        return_code = self.run()
        return(self.pos, self.judge(return_code))

class NarrowDown(object):
    def __init__(self, process_num, obj_list):
        self.__process_num = process_num
        self.__obj_list = obj_list
        self.__pool = multiprocessing.Pool(process_num)
        self.__L = multiprocessing.Manager().Value('i', 0)
        self.__R = multiprocessing.Manager().Value('i', len(obj_list))
        self.__gap = len(obj_list) // process_num
        self.__q = multiprocessing.Manager().Queue(process_num)
        self.__pos = 0

    def __run(self):
        while self.__L.value < self.__R.value:
            while self.__q.full():
                print ("wait for 1 sec")
                time.sleep(1)

            if self.__L.value < self.__R.value:
                if self.__pos < self.__L.value or self.__pos >= self.__R.value:
                    self.__pos = self.__L.value
                find = False
                while self.__pos < self.__R.value: 
                    if not self.__obj_list[self.__pos].visit():
                        find = True
                        self.__q.put(self.__pos)
                        print ("put " + str(self.__pos))
                        self.__pool.apply_async(run_tc,
                                                args=(self.__obj_list[self.__pos], ),
                                                callback=(self.__callback)
                                                )
                        self.__pos += self.__gap
                        break
                    elif self.__gap == 0:
                        break
                    else:
                        self.__pos += self.__gap
                if not find:
                    # choose in order
                    for i in list(range(self.__L.value, self.__R.value)):
                        if not self.__obj_list[i].visit():
                            find = True
                            self.__q.put(i)
                            print ("put " + str(i))
                            self.__pool.apply_async(run_tc,
                                                    args=(self.__obj_list[i], ),
                                                    callback=(self.__callback)
                                                    )
                            break
                if not find:
                    print ("all take up")
                    while self.__L.value < self.__R.value:
                        print ("sleep for 1 sec")
                        time.sleep(1)
            else:
                break
        self.__pool.terminate()
        self.__pool.join()
        print ("terminate")
        print ("L : " + str(self.__L.value) + " R : " + str(self.__R.value))

    def __callback(self, args):
        pos = args[0]
        is_pass = args[1]
        print ("list " + str(pos) + " quit with " + str(is_pass))
        if pos >= self.__L.value and pos <= self.__R.value:
            if is_pass:
                # pass
                self.__L.value = pos + 1
            else:
                self.__R.value = pos
            self.__gap = (self.__R.value - self.__L.value) // self.__process_num
        print ("current bound L: " + str(self.__L.value) + " R: " + str(self.__R.value))
        self.__q.get()
    
    def narrow_down(self):
        return self.__run()
