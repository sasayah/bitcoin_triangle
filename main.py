# -*- coding: utf-8 -*-
import sys
import json
import urllib.request
import itertools
import os


def getprice(coina,coinb):
    print('---------')
    if coina == coinb:
        return {'success': True, 'message': '', 'result': {'Bid': 1.0, 'Ask': 1.0, 'Last': 1.0}}
    try:
        url = 'https://bittrex.com/api/v1.1/public/getticker?market=' + coina + '-' + coinb
        res = urllib.request.urlopen(url)
        # json_loads() でPythonオブジェクトに変換
        data = json.loads(res.read().decode('utf-8'))
        if data['success'] == True:
            return data
        else:
            new_url = 'https://bittrex.com/api/v1.1/public/getticker?market=' + coinb + '-' + coina
            new_res = urllib.request.urlopen(new_url)
            new_data = json.loads(new_res.read().decode('utf-8'))
            if new_data['success'] == True:
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
    except urllib.error.HTTPError as e:
        print('HTTPError: ', e)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print('JSONDecodeError: ', e)
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

        
def buy_coin(coina, coinb, quantity, rate):
    try:
        url = 'https://bittrex.com/api/v1.1/market/buylimit?apikey=' + os.environ["API_KEY"] + '&market=' + coina + '-' + coinb + '&quantity=' + str(quantity) +'&rate=' + str(rate)
        res = urllib.request.urlopen(url)
        data = json.loads(res.read().decode('utf-8'))
        return data
    except urllib.error.HTTPError as e:
        print('HTTPError: ', e)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print('JSONDecodeError: ', e)
        sys.exit(1)



def main():
    coinlist = ['ETH', 'BTC', 'USDT', 'LTC']
    max_profit_list, true_reverse, max_profit = search_max_profit(coinlist)
    print(buy_coin("BTC","ETH",100,999))
    # print(list(itertools.combinations(coinlist, 3)))


main()