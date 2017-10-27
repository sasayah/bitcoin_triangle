# -*- coding: utf-8 -*-
from joblib import Parallel, delayed
from time import time

def process(n):
    return sum([i*n for i in range(100000)])

start = time()

# 繰り返し計算 (並列化)
r = Parallel(n_jobs=-1)( [delayed(process)(i) for i in range(10000)] )
print(sum(r))

print('{}秒かかりました'.format(time() - start))


def search_max_profit(coinlist):
    max_profit_list = ['','','']
    max_profit = 0.0
    true_reverse = True
    coin_pairs = list(itertools.combinations(coinlist, 3))
    trade_coin_pairs = []
    for coin_pair in coin_pairs:
        if check_coin_pair_anailable(coin_pair):
            trade_coin_pairs.append(coin_pair)

    def parallel_connect(coin_pair):
        profit, true_reverse = triangle_trade_profit(coin_pair[0],coin_pair[1],coin_pair[2])
        if  max_profit < profit:
            max_profit = profit
            max_profit_list = coin_pair

    Parallel(n_jobs=-1)( [delayed(process)(coin_pair) for coin_pair in trade_coin_pairs])
    return (max_profit_list, true_reverse, max_profit)
