# -*- coding: utf-8 -*-
import numpy as np
import sys
import json
import urllib.request
import itertools
import os
from time import sleep
import time
import hmac
import hashlib
from joblib import Parallel, delayed
from multiprocessing import Value, Array

#input  coina, coinb, sell_coina_amount
#output rate
#static n_times 何倍まで許すか
json = {"success":True,"message":"","result":{"buy":[{"Quantity":68.64920495,"Rate":0.00928601},{"Quantity":63.01240000,"Rate":0.00928600},{"Quantity":7.51787831,"Rate":0.00928113},{"Quantity":0.39364571,"Rate":0.00928067},{"Quantity":1.30696350,"Rate":0.00928017},{"Quantity":24.37446121,"Rate":0.00928000},{"Quantity":0.20386393,"Rate":0.00927922},{"Quantity":0.94995260,"Rate":0.00927888},{"Quantity":0.47274640,"Rate":0.00927817},{"Quantity":0.29013726,"Rate":0.00927785},{"Quantity":0.21525476,"Rate":0.00927771},{"Quantity":0.27856924,"Rate":0.00927662}],"sell":[{"Quantity":5861.72913582,"Rate":0.00929781},{"Quantity":0.29017865,"Rate":0.00929812},{"Quantity":1.50000000,"Rate":0.00929981},{"Quantity":0.90000000,"Rate":0.00930000},{"Quantity":0.54940052,"Rate":0.00930209},{"Quantity":4.00000000,"Rate":0.00931000},{"Quantity":0.13878676,"Rate":0.00931225},{"Quantity":1.00000000,"Rate":0.00931827},{"Quantity":0.92698861,"Rate":0.00932187}]}}

print(json['result']['buy'][0])

def decide_trade_rate(coina, coinb, sell_coina_amount):
    sum_a_cost = 0
    last_rate = 0
    n_times = 2 # 何倍まで取引に余裕を持たせるか.調整必要
    url = 'https://bittrex.com/api/v1.1/public/getorderbook?'
    url += 'market=' + coina + '-' + coinb
    url += '&type=both'
    order_book_data = get_json_data(url)
    if order_book_data['success']:
        for order_data in order_book_data['result']['buy']:
            sum_a_cost += order_data['Quantity'] * order_data['Rate']
            last_rate = order_data['Rate']
            if sum_a_cost > sell_coina_amount * n_times:
                break
    else:
        for order_data in order_book_data['result']['sell']:
            sum_a_cost += order_data['Quantity']
            last_rate = 1 / order_data['Rate']
            if sum_a_cost > sell_coina_amount * n_times:
                break
    return last_rate





