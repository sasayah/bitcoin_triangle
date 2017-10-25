import hmac
import hashlib
import requests
import os
import json
import urllib.request
import time
import sys

    

def get_url(api):
    url = 'https://bittrex.com/api/v1.1/account/'
    url += api + '?'
    url += 'apikey=' + os.environ["API_KEY"]
    url += '&nonce=' + str(int(time.time()))


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




coina = 'ETH'
url = 'https://bittrex.com/api/v1.1/account/getbalance?'
url += 'apikey=' + os.environ["API_KEY"]
url += '&currency=' + coina
url += '&nonce=' + str(int(time.time()))

data = get_json_key_data(url)
print(data)
url = 'https://bittrex.com/api/v1.1/public/getticker?market=BTC-ETH'
data = get_json_data(url)
print(data)
