#!/usr/local/bin/python3

def test(num):
    in_num = num
    def nested(label):
        nonlocal in_num
        in_num += 1
        print(in_num, label)
    return nested
