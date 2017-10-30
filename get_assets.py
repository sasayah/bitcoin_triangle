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

    nexta = coinc_volume / getprice_c_a['Ask']
    nextb = coina_volume / getprice_a_b['Ask']
    nextc = coinb_volume / getprice_b_c['Ask']
    profit = (nexta-coina_volume)/coina_volume + (nextb-coinb_volume)/coinb_volume + (nextc-coinc_volume)/coinc_volume
    
    reverse_nexta = coinb_volume * getprice_a_b['Bid']
    reverse_nextb = coinc_volume * getprice_b_c['Bid']
    reverse_nextc = coina_volume * getprice_c_a['Bid']
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
    max_profit_list = search_results[max_index][2]
    if max_profit < miniprofit:
        max_profit = 0.0
    return (max_profit_list, max_profit_list, max_profit)

def buy_coin(coina, coinb, quantity, rate):
    url = 'https://bittrex.com/api/v1.1/market/buylimit?apikey=' 
    url += os.environ["API_KEY"] 
    url += '&market=' + coina + '-' + coinb 
    url += '&quantity=' + str(quantity) 
    url += '&rate=' + str(rate)
    data = get_json_key_data(url)
    return data


#　現在のコイン保有量を取得
def account_money_amount(coina,coinb,coinc):
    url_a = 'https://bittrex.com/api/v1.1/account/getbalance?apikey=' + os.environ["API_KEY"] + '&currency=' + coina
    url_b = 'https://bittrex.com/api/v1.1/account/getbalance?apikey=' + os.environ["API_KEY"] + '&currency=' + coinb
    url_c = 'https://bittrex.com/api/v1.1/account/getbalance?apikey=' + os.environ["API_KEY"] + '&currency=' + coinc
    
    data_a = get_json_key_data(url_a)
    data_b = get_json_key_data(url_b)
    data_c = get_json_key_data(url_c)
    #現在所有のビットコインを確定!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if data_a['result']['Balance'] == None:
        curretn_coin_a_ammout = 0.0
    else:
        curretn_coin_a_ammout = data_a['result']['Balance']
    if data_b['result']['Balance'] == None:
        curretn_coin_b_ammout = 0.0
    else:
        curretn_coin_b_ammout = data_b['result']['Balance']
    if data_c['result']['Balance'] == None:
        curretn_coin_c_ammout = 0.0
    else:
        curretn_coin_c_ammout = data_c['result']['Balance']

    return (curretn_coin_a_ammout, curretn_coin_b_ammout, curretn_coin_c_ammout)

def cancel_trade(uuid):
    url = 'https://bittrex.com/api/v1.1/market/cancel?apikey=' + os.environ["API_KEY"] + '&uuid=' + uuid
    data = get_json_key_data(url)
    return data


def execute_triangle(coinlist,miniprofit):
    max_profit_list, true_reverse, max_profit = search_max_profit(coinlist, miniprofit)
    if max_profit > miniprofit:
        coina = max_profit_list[0]
        coinb = max_profit_list[1]
        coinc = max_profit_list[2]
        if not true_reverse:
            max_profit_list[0], max_profit_list[1] = max_profit_list[1], max_profit_list[0]
        getprice_c_a = getprice(coinc,coina)['result']
        getprice_a_b = getprice(coina,coinb)['result']
        getprice_b_c = getprice(coinb,coinc)['result']
        curretn_coin_a_ammout, curretn_coin_b_ammout, curretn_coin_c_ammout = account_money_amount(coina,coinb,coinc)
        #ここは三種類の価値を統一にすべき
        sell_coin_a_amount = curretn_coin_a_ammout * 0.8
        sell_coin_b_amount = curretn_coin_b_ammout * 0.8
        sell_coin_c_amount = curretn_coin_c_ammout * 0.8

        buy_coin_a_amoutn = sell_coin_c_amount / getprice_c_a['Ask']
        buy_coin_b_amoutn = sell_coin_a_amount / getprice_a_b['Ask']
        buy_coin_c_amoutn = sell_coin_b_amount / getprice_b_c['Ask']
        
        trade_data_a = buy_coin(coinc, coina, buy_coin_a_amoutn, getprice_c_a['Ask'])
        trade_data_b = buy_coin(coina, coinb, buy_coin_b_amoutn, getprice_a_b['Ask'])
        trade_data_c = buy_coin(coinb, coinc, buy_coin_c_amoutn, getprice_b_c['Ask'])

        # 暫定的に、3秒待って約定しなかったらキャンセル
        sleep(3)
        cancel_trade(trade_data_a['result']['uuid'])
        cancel_trade(trade_data_b['result']['uuid'])
        cancel_trade(trade_data_c['result']['uuid'])


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
    coinlist = ['ETH', 'BTC', 'USDT', 'XRP', 'XMR', 'NEO', 'BCC', 'LTC']
    miniprofit = 0.001
    #account_money_amount('ETH', 'BTC', 'USDT')
    #max_profit_list, true_reverse, max_profit = search_max_profit(coinlist)
    #print(buy_coin("BTC","ETH",100,999))
    #print(list(itertools.combinations(coinlist, 3)))
    #print(search_max_profit(coinlist))
    """
    while(1):
        execute_triangle(coinlist,miniprofit)
    
    """
    first_money = 0.0
    pre_money = 0.0
    multi_roop = False

    first_eth, first_btc, first_usdt = account_money_amount('ETH', 'BTC', 'USDT')
    first_xrp, first_xmr, first_neo = account_money_amount('XRP', 'XMR', 'NEO')
    first_bcc, first_LTC, first_a = account_money_amount('BCC', 'LTC', 'NEO')

    pre_eth = first_eth
    pre_btc = first_btc
    pre_usdt = first_usdt
    pre_xrp = first_xrp
    pre_xmr = first_xmr
    pre_neo = first_neo
    pre_bcc = first_bcc
    pre_LTC = first_LTC

    while(1):
        eth, btc, usdt = account_money_amount('ETH', 'BTC', 'USDT')
        xrp, xmr, neo = account_money_amount('XRP', 'XMR', 'NEO')
        bcc, LTC, a = account_money_amount('BCC', 'LTC', 'NEO')

        money = 0.0
        eth_price = eth/getprice("ETH","BTC")['result']['Ask']
        btc_price = btc/getprice("BTC","BTC")['result']['Ask']
        usdt_price = usdt/getprice("USDT","BTC")['result']['Ask']
        xrp_price = xrp/getprice("XRP","BTC")['result']['Ask']
        bcc_price = bcc/getprice("BCC","BTC")['result']['Ask']
        ltc_price = LTC/getprice("LTC","BTC")['result']['Ask']
        neo_price = neo/getprice("NEO","BTC")['result']['Ask']
        xmr_price = xmr/getprice("XMR","BTC")['result']['Ask']
    
        money = eth_price + btc_price + usdt_price + xrp_price + bcc_price + ltc_price + neo_price + xmr_price

        print("eth: " + str(eth) + ', btc: ' + str(eth_price) + '(BTC), pre_diff: ' + str(eth - pre_eth) + '(ETH), total_diff: ' +str(eth - first_eth) + '(ETH)')
        print("btc: " + str(btc) + ', btc: ' + str(btc_price) + '(BTC), pre_diff: ' + str(btc - pre_btc) + '(BTC), total_diff: ' +str(btc - first_btc) + '(BTC)')
        print("usdt: " + str(usdt) + ', btc: ' + str(usdt_price) + '(BTC), pre_diff: ' + str(usdt - pre_usdt) + '(USDT), total_diff: ' +str(usdt - first_usdt) + '(USDT)')
        print("xrp: " + str(xrp) + ', btc: ' + str(xrp_price) + '(BTC), pre_diff: ' + str(xrp - pre_xrp) + '(XRP), total_diff: ' +str(xrp - first_xrp) + '(XRP)')
        print("bcc: " + str(bcc) + ', btc: ' + str(bcc_price) + '(BTC), pre_diff: ' + str(bcc - pre_bcc) + '(BCC), total_diff: ' +str(bcc - first_bcc) + '(BCC)')
        print("LTC: " + str(LTC) + ', btc: ' + str(ltc_price) + '(BTC), pre_diff: ' + str(LTC - pre_LTC) + '(LTC), total_diff: ' +str(LTC - first_LTC) + '(LTC)')
        print("neo: " + str(neo) + ', btc: ' + str(neo_price) + '(BTC), pre_diff: ' + str(neo - pre_neo) + '(NEO), total_diff: ' +str(neo - first_neo) + '(NEO)')
        print("xmr: " + str(xmr) + ', btc: ' + str(xmr_price) + '(BTC), pre_diff: ' + str(xmr - pre_xmr) + '(XMR), total_diff: ' +str(xmr - first_xmr) + '(XMR)')

        print('Total: ' + str(money) + "(BTC)")

        min_btc_value = money / 12

        if not multi_roop:
            first_money = money

        print('diff: ' + str(money - pre_money))
        print('totaldiff: ' + str(money - first_money))
        multi_roop = True

        pre_money = money

        print("")
        print("")
        print("")
        print("")
        print("")
        print("")


        if eth_price < min_btc_value or btc_price < min_btc_value or usdt_price < min_btc_value or xrp_price < min_btc_value or bcc_price < min_btc_value or ltc_price < min_btc_value:
            print("Error")
            print("Error")
            print("Error")
            print("Error")
            print("Error")
            print("Error")
            print("Error")
            print("Error")
            print("Error")

main()