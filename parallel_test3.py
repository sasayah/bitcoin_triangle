#! /usr/local/bin/python
# -*- coding:utf-8

import multiprocessing
from time import sleep

def foo():
    def f(j,k):
        l = j + k
        print ("no:%s" % i)
        sleep(5 - i)
        print ("unko%s" % l)
   # jobs = []
    for i in range(5):
        p = multiprocessing.Process(target=f,args=(i,100))
     #   jobs.append(p)
        p.start()
        #print(jobs)
foo()