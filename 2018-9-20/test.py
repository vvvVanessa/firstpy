import multiprocessing
from random import randint
import time

class mycls(object):
    def __init__(self, pos):
        self.value = randint(2, 7)
        self.vis = False
        self.pos = pos
        self.result = 0 if self.pos < bp else 1
    def run(self):
        time.sleep(self.value)
    def visit(self):
        if not self.vis:
            self.vis = True
            return False
        else:
            return True
    def callback(self, quit_code):
        print ("mycls " + str(self.pos) + " quit with " + str(quit_code))
        if self.pos >= L.value and self.pos <= R.value:
            if self.result == 0:
                # fail
                L.value = self.pos + 1
            else:
                R.value = self.pos
            gap = (R.value - L.value) / div
        print ("current bound L: " + str(L.value) + " R: " + str(R.value))
        q.get()

def run_tc(obj):
    obj.run()
    return 11

if __name__ == '__main__':
    div = int(input("input parallel process number: "))
    llen = int(input("input the length of list: "))
    bp = int(input("input the breakpoint: "))

    if div > llen:
        div = llen

    mycls_list = []
    for i in range(llen):
        mycls_list.append(mycls(i))

    pool = multiprocessing.Pool(div)
    q = multiprocessing.Manager().Queue(div)
    L = multiprocessing.Manager().Value('i', 0)
    R = multiprocessing.Manager().Value('i', (len(mycls_list)))

    gap = (R.value - L.value) / div
    pos = 0
    while L.value < R.value:
        while q.full():
            print ("sleep for 1 sec")
            time.sleep(1)
        if L.value < R.value:
            if pos < L.value or pos >= R.value:
                pos = L.value
            find = False
            while pos < R.value:
                if not mycls_list[pos].visit():
                    find = True
                    q.put(pos)
                    print("put " + str(pos))
                    pool.apply_async(run_tc,
                                     args=(mycls_list[pos], ),
                                     callback=mycls_list[pos].callback)
                    pos = pos + gap
                    break
                else:
                    pos = pos + gap
            if not find:
                # choose in order
                for i in list(range(L.value, R.value)):
                    if not mycls_list[i].visit():
                        find = True
                        q.put(i)
                        print("put " + str(i))
                        pool.apply_async(run_tc, 
                                         args=(mycls_list[i], ),
                                         callback=mycls_list[i].callback)
                        break
            if not find: # still not find, which means no rest to be added
                print ("all take up")
                # break the main loop
                while(L.value < R.value):
                    print ("sleep for 1 sec")
                    time.sleep(1)
        else:
            break
    # pool.close()
    pool.terminate()
    pool.join()
    print ("-terminate.")
    print ("L: " + str(L.value) + " R: " + str(R.value))
    print ("guess your break point is: " + str(L.value))
