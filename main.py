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

sleep_time = 5
trade_fee = 0.001

def getprice(coina,coinb):
    if coina == coinb:
        return {'success': True, 'message': '', 'result': {'Bid': 1.0, 'Ask': 1.0, 'Last': 1.0}}
    url = 'https://bittrex.com/api/v1.1/public/getticker?market=' + coina + '-' + coinb
    data = get_json_data(url)
    if data['success']:
        return data
    else:
        new_url = 'https://bittrex.com/api/v1.1/public/getticker?market=' + coinb + '-' + coina
        new_data = get_json_data(new_url)
        if new_data['success']:
            last_data = new_data
            previous_bid = new_data['result']['Bid']
            previous_ask = new_data['result']['Ask']
            previous_last = new_data['result']['Last']
            last_data['result']['Bid'] = 1 / previous_ask
            last_data['result']['Ask'] = 1 / previous_bid
            last_data['result']['Last'] = 1 / previous_last
            return last_data
        else:
            print("Invalid json response")
            sys.exit(1)

# coina -> coinb -> coinc　でそれぞれ1bitcoinの価値あたりで取引
def triangle_trade_profit(coinlist):
    coina = coinlist[0]
    coinb = coinlist[1]
    coinc = coinlist[2]
    coina_volume = getprice(coina,'BTC')['result']['Ask']
    coinb_volume = getprice(coinb,'BTC')['result']['Ask']
    coinc_volume = getprice(coinc,'BTC')['result']['Ask']

    getprice_c_a = getprice(coinc,coina)['result']
    getprice_a_b = getprice(coina,coinb)['result']
    getprice_b_c = getprice(coinb,coinc)['result']
# trade_feeを考慮
    nexta = (coinc_volume / getprice_c_a['Ask']) *(1-trade_fee)
    nextb = (coina_volume / getprice_a_b['Ask']) *(1-trade_fee)
    nextc = (coinb_volume / getprice_b_c['Ask']) *(1-trade_fee)
    profit = (nexta-coina_volume)/coina_volume + (nextb-coinb_volume)/coinb_volume + (nextc-coinc_volume)/coinc_volume
    
    reverse_nexta = coinb_volume * getprice_a_b['Bid'] * (1-trade_fee)
    reverse_nextb = coinc_volume * getprice_b_c['Bid'] * (1-trade_fee)
    reverse_nextc = coina_volume * getprice_c_a['Bid'] * (1-trade_fee)
    reverse_profit = (reverse_nexta-coina_volume)/coina_volume + (reverse_nextb-coinb_volume)/coinb_volume + (reverse_nextc-coinc_volume)/coinc_volume
    
    # print(profit)
    # print(reverse_profit)
    if profit > reverse_profit:
        return (profit,True,coinlist)
    else:
        return (reverse_profit,False,coinlist)

#print(getprice('ETH', 'USDT'))
#print(getprice('BTC', 'USDT'))
#print(triangle_trade_profit('BTC', 'ETH', 'USDT'))
#print(triangle_trade_profit('ETH', 'BTC', 'USDT'))

def check_coin_pair_anailable(coin_pair):
    check = 0
    for coin in coin_pair:
        if coin in ['ETH', 'BTC', 'USDT']:
            check += 1
    if check >= 2:
        return True
    else:
        return False


def search_max_profit(coinlist, miniprofit):
    coin_pairs = list(itertools.combinations(coinlist, 3))
    trade_coin_pairs = []
    for coin_pair in coin_pairs:
        if check_coin_pair_anailable(coin_pair):
            trade_coin_pairs.append(coin_pair)
    search_results = Parallel(n_jobs=-1)( [delayed(triangle_trade_profit)(coin_pair) for coin_pair in trade_coin_pairs])
    search_max_index = []
    for search_result in search_results:
        search_max_index.append(search_result[0])
    max_index = search_max_index.index(max(search_max_index))
    max_profit = search_results[max_index][0]
    true_reverse = search_results[max_index][1]
    max_profit_list = list(search_results[max_index][2])
    print('profit: ' + str(max_profit))
    print(max_profit_list)
    if max_profit < miniprofit:
        max_profit = 0.0
    return (max_profit_list, true_reverse, max_profit)

def buy_coin(coina, coinb, quantity, rate):
    url = 'https://bittrex.com/api/v1.1/market/buylimit?apikey=' 
    url += os.environ["API_KEY"] 
    url += '&market=' + coina + '-' + coinb 
    url += '&quantity=' + str(quantity) 
    url += '&rate=' + str(rate)
    data = get_json_key_data(url)
    print(coina +','+ coinb +': quantity: '+ str(quantity),': rate :', str(rate))
    if data['result']:
        return data
    else:
        url = 'https://bittrex.com/api/v1.1/market/selllimit?apikey=' 
        url += os.environ["API_KEY"]
        url += '&market=' + coinb + '-' + coina
        url += '&quantity=' + str(quantity*rate) 
        url += '&rate=' + str(1/rate)
        data = get_json_key_data(url)
        return data


        

def decide_trade_amount(coina, coina_amount, coinb, coinb_amount, coinc, coinc_amount):
    trade_parcent = 0.8
    coina_value_btc = coina_amount * getprice("BTC",coina)['result']['Ask']
    coinb_value_btc = coinb_amount * getprice("BTC",coinb)['result']['Ask']
    coinc_value_btc = coinc_amount * getprice("BTC",coinc)['result']['Ask']
    min_value = min(coina_value_btc, coinb_value_btc, coinc_value_btc)
    print("min_value: " + str(min_value))
    if min_value > 0.0006:
        trade_a_amount = trade_parcent * (coina_amount * min_value / coina_value_btc)
        trade_b_amount = trade_parcent * (coinb_amount * min_value / coinb_value_btc)
        trade_c_amount = trade_parcent * (coinc_amount * min_value / coinc_value_btc)
        return (trade_a_amount, trade_b_amount, trade_c_amount)
    else:
        return (0.0,0.0,0.0)

def account_money_amount(coina):
    url = 'https://bittrex.com/api/v1.1/account/getbalance?apikey=' + os.environ["API_KEY"] + '&currency=' + coina
    data = get_json_key_data(url)
    if data['result']['Balance'] == None:
        curretn_coin_ammout = 0.0
    else:
        curretn_coin_ammout = data['result']['Balance']

    return curretn_coin_ammout

#　現在のコイン保有量を取得
def account_money_amounts(coina,coinb,coinc):

    curretn_coin_a_ammout = account_money_amount(coina)
    curretn_coin_b_ammout = account_money_amount(coinb)
    curretn_coin_c_ammout = account_money_amount(coinc)

    return (curretn_coin_a_ammout, curretn_coin_b_ammout, curretn_coin_c_ammout)


def cancel_trade(uuid):
    url = 'https://bittrex.com/api/v1.1/market/cancel?apikey=' + os.environ["API_KEY"] + '&uuid=' + uuid
    data = get_json_key_data(url)
    return data

def true_profit(coina, coinb, coinc, buy_coin_a_amount, buy_coin_b_amount, buy_coin_c_amount, getprice_c_a, getprice_a_b, getprice_b_c):
    coina_diff = buy_coin_a_amount * (1-trade_fee) - buy_coin_b_amount*getprice_a_b
    coinb_diff = buy_coin_b_amount * (1-trade_fee) - buy_coin_c_amount*getprice_b_c
    coinc_diff = buy_coin_c_amount * (1-trade_fee) - buy_coin_a_amount*getprice_c_a
    print('coina_diff: ' + str(coina_diff))
    print('coinb_diff: ' + str(coinb_diff))
    print('coinc_diff: ' + str(coinc_diff))
    
    coina_profit = coina_diff * getprice("BTC",coina)['result']['Last']
    coinb_profit = coinb_diff * getprice("BTC",coinb)['result']['Last']
    coinc_profit = coinc_diff * getprice("BTC",coinc)['result']['Last']
    sum_profit = coina_profit + coinb_profit + coinc_profit
    print(coina + ': ' + str(getprice("BTC",coina)['result']['Last']) + '(BTC) ,' + "buy_coin_a_amount: " + str(buy_coin_a_amount))
    print(coinb + ': ' + str(getprice("BTC",coinb)['result']['Last']) + '(BTC) ,' + "buy_coin_b_amount: " + str(buy_coin_b_amount))
    print(coinc + ': ' + str(getprice("BTC",coinc)['result']['Last']) + '(BTC) ,' + "buy_coin_c_amount: " + str(buy_coin_c_amount))
    print("getprice_c_a: " + str(getprice_c_a))
    print("getprice_a_b: " + str(getprice_a_b))
    print("getprice_b_c: " + str(getprice_b_c))
    
    return sum_profit

#本当にうまく動いているのか確認!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def decide_trade_rate(coina, coinb, sell_coina_amount):
    sum_a_cost = 0
    last_rate = 0
    n_times = 1.2 # 何倍まで取引に余裕を持たせるか.調整必要
    url = 'https://bittrex.com/api/v1.1/public/getorderbook?'
    url += 'market=' + coina + '-' + coinb
    url += '&type=both'
    order_book_data = get_json_data(url)
    if order_book_data['success']:
        for order_data in order_book_data['result']['sell']:
            sum_a_cost += order_data['Quantity'] * order_data['Rate']
            last_rate = order_data['Rate']
            if sum_a_cost > sell_coina_amount * n_times:
                break
    else:
        url = 'https://bittrex.com/api/v1.1/public/getorderbook?'
        url += 'market=' + coinb + '-' + coina
        url += '&type=both'
        order_book_data = get_json_data(url)

        for order_data in order_book_data['result']['buy']:
            sum_a_cost += order_data['Quantity']
            last_rate = 1 / order_data['Rate']
            if sum_a_cost > sell_coina_amount * n_times:
                break
    return last_rate


def execute_triangle(coinlist,miniprofit):
    max_profit_list, true_reverse, max_profit = search_max_profit(coinlist, miniprofit)
    if max_profit < miniprofit:
        return 0.0
    else:
        coina = max_profit_list[0]
        coinb = max_profit_list[1]
        coinc = max_profit_list[2]
        print(str(true_reverse) + 'aaaaaaaaaaaaaaaaaaaa')
        if not true_reverse:
            coina, coinb = coinb, coina
        curretn_coin_a_amount, curretn_coin_b_amount, curretn_coin_c_amount = account_money_amounts(coina,coinb,coinc)
        sell_coin_a_amount, sell_coin_b_amount, sell_coin_c_amount = decide_trade_amount(coina, curretn_coin_a_amount, coinb, curretn_coin_b_amount, coinc, curretn_coin_c_amount)
        trade_c_a_rate = decide_trade_rate(coinc, coina, sell_coin_c_amount)
        trade_a_b_rate = decide_trade_rate(coina, coinb, sell_coin_a_amount)
        trade_b_c_rate = decide_trade_rate(coinb, coinc, sell_coin_b_amount)
        '''
        getprice_c_a = getprice(coinc,coina)['result']
        getprice_a_b = getprice(coina,coinb)['result']
        getprice_b_c = getprice(coinb,coinc)['result']
        '''
        if sell_coin_a_amount <= 0:
            return 0.0

        else:

            buy_coin_a_amount = sell_coin_c_amount / trade_c_a_rate
            buy_coin_b_amount = sell_coin_a_amount / trade_a_b_rate
            buy_coin_c_amount = sell_coin_b_amount / trade_b_c_rate

            print('aの差: ' + str(buy_coin_a_amount - sell_coin_a_amount))
            print('bの差: ' + str(buy_coin_b_amount - sell_coin_b_amount))
            print('cの差: ' + str(buy_coin_c_amount - sell_coin_c_amount))

            '''#####################
            coin_a_last_rate = decide_trade_rate(coinc, coina, sell_coin_c_amount)
            coin_b_last_rate = decide_trade_rate(coina, coinb, sell_coin_a_amount)
            coin_c_last_rate = decide_trade_rate(coinb, coinc, sell_coin_b_amount)
            print('getprice c-a: ' + str(getprice_c_a['Ask']) + ', lastprice:' + str(coin_a_last_rate))
            print('getprice a-b: ' + str(getprice_a_b['Ask']) + ', lastprice:' + str(coin_b_last_rate))
            print('getprice b-c: ' + str(getprice_b_c['Ask']) + ', lastprice:' + str(coin_c_last_rate))
            #####################'''

            sum_profit = true_profit(coina, coinb, coinc, buy_coin_a_amount, buy_coin_b_amount, buy_coin_c_amount, trade_c_a_rate, trade_a_b_rate, trade_b_c_rate)
            print("true_profit: " + str(sum_profit))
            if sum_profit < 0:
                return 0.0
            else:
                trade_data_a = buy_coin(coinc, coina, buy_coin_a_amount, trade_c_a_rate)
                trade_data_b = buy_coin(coina, coinb, buy_coin_b_amount, trade_a_b_rate)
                trade_data_c = buy_coin(coinb, coinc, buy_coin_c_amount, trade_b_c_rate)

                if not (trade_data_a['success'] and trade_data_b['success'] and trade_data_c['success']):
                    print(trade_data_a)
                    print(trade_data_b)
                    print(trade_data_c)

                # 暫定的に、5秒待って約定しなかったらキャンセル
                sleep(sleep_time)
                cancel_a = cancel_trade(trade_data_a['result']['uuid'])
                cancel_b = cancel_trade(trade_data_b['result']['uuid'])
                cancel_c = cancel_trade(trade_data_c['result']['uuid'])

                if not(cancel_a['success'] or cancel_b['success'] or cancel_c['success']):
                    return sum_profit

                else:
                    print(cancel_a)
                    print(cancel_b)
                    print(cancel_c)
                    
                    if cancel_a['success']:
                        retry_trade(coinc, coina, sell_coin_c_amount)
                    if cancel_b['success']:
                        retry_trade(coina, coinb, sell_coin_a_amount)
                    if cancel_c['success']:
                        retry_trade(coinb, coinc, sell_coin_b_amount)
                    return 0.0           


def retry_trade(coina, coinb, sell_coin_a_amount):
    while(1):
        trade_a_b_rate = decide_trade_rate(coina, coinb, sell_coin_a_amount)
        buy_coin_b_amount = sell_coin_a_amount / trade_a_b_rate
        trade_data_b = buy_coin(coina, coinb, buy_coin_b_amount, trade_a_b_rate)
        sleep(sleep_time)
        cancel_b = cancel_trade(trade_data_b['result']['uuid'])
        if trade_data_b['success'] and (not cancel_b['success']):
            break


def get_json_data(url):
    try:
        res = urllib.request.urlopen(url)
        data = json.loads(res.read().decode('utf-8'))
        return data
    except urllib.error.HTTPError as e:
        print('HTTPError: ', e)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print('JSONDecodeError: ', e)
        sys.exit(1)


def get_json_key_data(url):
    try:
        url += '&nonce=' + str(int(time.time()))
        signing = hmac.new(os.environ["API_SECRET"].encode("UTF-8"), url.encode("UTF-8"), hashlib.sha512).hexdigest()
        headers = {'apisign': signing}
        res = urllib.request.Request(url, headers=headers)
        data = json.loads(urllib.request.urlopen(res).read())
        return data
    except urllib.error.HTTPError as e:
        print('HTTPError: ', e)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print('JSONDecodeError: ', e)
        sys.exit(1)


def main():
    coinlist = ['ETH', 'BTC', 'USDT', 'XRP', 'BCC', 'LTC', 'NEO', 'XMR']
    miniprofit = 0.0001
    sum_profit = 0.0
    
    while(1):
        profit = execute_triangle(coinlist,miniprofit)
        sum_profit += profit
        print("SUM PROFIT: " + str(sum_profit) + "(BTC)" )
    
    '''
    profit = execute_triangle(coinlist,miniprofit)
    sum_profit += profit
    print("SUM PROFIT: " + str(sum_profit) + "(BTC)" )
    '''
    
    """
    profit = 0.0
    while(1):
        max_profit_list, true_reverse, max_profit = search_max_profit(coinlist, miniprofit)
        profit += max_profit
        print(max_profit_list)
        print(max_profit)
        print(profit)
    """
    

main()