# -*- coding: utf-8 -*-
import sys
import json
import urllib.request
import itertools
import os
from time import sleep
import hmac
import hashlib



def getprice(coina,coinb):
    print('---------')
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
def triangle_trade_profit(coina, coinb, coinc):
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
        return (profit,True)
    else:
        return (reverse_profit,False)

#print(getprice('ETH', 'USDT'))
#print(getprice('BTC', 'USDT'))
#print(triangle_trade_profit('BTC', 'ETH', 'USDT'))
#print(triangle_trade_profit('ETH', 'BTC', 'USDT'))


def search_max_profit(coinlist):
    max_profit_list = ['','','']
    max_profit = 0.0
    true_reverse = True
    coin_pairs = list(itertools.combinations(coinlist, 3))
    for coin_pair in coin_pairs:
        profit, true_reverse = triangle_trade_profit(coin_pair[0],coin_pair[1],coin_pair[2])
        if  max_profit < profit:
            max_profit = profit
            max_profit_list = coin_pair
    return (max_profit_list, true_reverse, max_profit)

        #エラー処理!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!apiを叩くとこは全てエラー処理
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
    #現在所有のビットコインを確定!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print(url_a)
    print(data_a)
    curretn_coin_a_ammout = data_a['result']['Available']
    curretn_coin_b_ammout = data_b['result']['Available']
    curretn_coin_c_ammout = data_c['result']['Available']
    return (curretn_coin_a_ammout, curretn_coin_b_ammout, curretn_coin_c_ammout)

def cancel_trade(uuid):
    url = 'https://bittrex.com/api/v1.1/market/cancel?apikey=' + os.environ["API_KEY"] + '&uuid=' + uuid
    data = get_json_key_data(url)
    return data


def execute_triangle(coinlist,minprofit):
    max_profit_list, true_reverse, max_profit = search_max_profit(coinlist)
    if max_profit > minprofit:
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
    coinlist = ['ETH', 'BTC', 'USDT', 'LTC']
    minprofit = 0.001
    account_money_amount('ETH', 'BTC', 'USDT')
    #max_profit_list, true_reverse, max_profit = search_max_profit(coinlist)
    #print(buy_coin("BTC","ETH",100,999))
    #print(list(itertools.combinations(coinlist, 3)))
    #print(search_max_profit(coinlist))
    """
    while(;){
        execute_triangle(coinlist,minprofit)
    }
    """

main()