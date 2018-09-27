from myp import *
import time
from random import randint

class Myt(Target):
    def __init__(self, pos):
        super(Myt, self).__init__(pos)
        self.__value = randint(2, 7)
    
    def run(self):
        time.sleep(self.__value)
        return 11 if self.pos < bp else 10

    def judge(self, return_code):
        return True if return_code == 11 else False

if __name__ == "__main__":
    process_num = int(input("input parallel process number: "))
    llen = int(input("input the length of list: "))
    bp = int(input("input the breakpoint: "))

    if process_num > llen:
        process_num = llen

    obj_list = []
    for i in range(llen):
        obj_list.append(Myt(i))

    nd = NarrowDown(process_num, obj_list)
    nd.narrow_down()
