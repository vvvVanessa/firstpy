import multiprocessing
import time
from abc import abstractmethod

global L, R, q, process_num, gap
class Target(object):
    def __init__(self, pos, vis=False):
        self.pos = pos
        self.vis = vis

    def visit(self):
        if not self.vis:
            self.vis = True
            return False
        else:
            return True

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
    @abstractmethod
    def judge(self, quit_code):
        pass

    def run_and_judge(self):
        return_code = self.run()
        return (self.pos, self.judge(return_code))


def run_tc(obj):
    return obj.run_and_judge()

def callback(args):
    pos = args[0]
    is_pass = args[1]
    print "list " + str(pos) + " quit with " + str(is_pass)
    if pos >= L.value and pos <= R.value:
        if is_pass == True:
            # pass
            L.value = pos + 1
        else:
            R.value = pos
        gap = (R.value - L.value) / process_num
    print "current bound L: " + str(L.value) + " R: " + str(R.value)
    q.get()

def narrow_down(process_num, obj_list):

    if process_num > len(obj_list):
        process_num = len(obj_list)

    pos = 0

    pool = multiprocessing.Pool(process_num)
    q = multiprocessing.Manager().Queue(process_num)
    L = multiprocessing.Manager().Value('i', 0)
    R = multiprocessing.Manager().Value('i', len(obj_list))
    gap = (R.value - L.value) / process_num
    while L.value < R.value:
        while q.full():
            print "sleep for 1 sec"
            time.sleep(1)
        # run_cnt += 1
        if L.value < R.value:
            if pos < L.value or pos >= R.value:
                pos = L.value
            find = False
            while pos < R.value:
                if not obj_list[pos].visit():
                    find = True
                    q.put(pos)
                    print"put " + str(pos)
                    pool.apply_async(run_tc,
                                     args=(obj_list[pos], ), 
                                     callback=callback)
                    pos = pos + gap
                    break
                else:
                    pos = pos + gap
            if not find:
                # choose in order
                for i in list(range(L.value, R.value)):
                    if not obj_list[i].visit():
                        find = True
                        q.put(i)
                        print"put " + str(i)
                        pool.apply_async(run_tc, 
                                         args=(obj_list[i], ),
                                         callback=callback)
                        break
            if not find: # still not find, which means no rest to be added
                print "all take up"
                # break the main loop
                while(L.value < R.value):
                    print "sleep for 1 sec"
                    time.sleep(1)
        else:
            break
    # pool.close()
    pool.terminate()
    pool.join()
    print "-terminate "
    print "L: " + str(L.value) + " R: " + str(R.value)

