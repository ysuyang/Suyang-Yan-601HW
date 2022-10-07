import time
import os
import requests
from requests.adapters import HTTPAdapter
import botometer
from tqdm import tqdm
import json

bearar = os.environ['BEARAR_TOKEN']
BEARAR_TOKEN = f'Bearer {bearar}'
HEADERS = {
    'Authorization': BEARAR_TOKEN
}
TIMEOUT = 5

RAPIDAPI_KEY = os.environ['RAPIDAPI_KEY']
TWI_APP_AUTH = {
    'consumer_key': os.environ['consumer_key'],
    'consumer_secret': os.environ['consumer_secret'],
    'access_token': os.environ['access_token'],
    'access_token_secret': os.environ['access_token_secret'],
}
bom = botometer.Botometer(wait_on_ratelimit=True,
                          rapidapi_key=RAPIDAPI_KEY,
                          **TWI_APP_AUTH)

session = requests.Session()
session.mount('http://', HTTPAdapter(max_retries=3))
session.mount('https://', HTTPAdapter(max_retries=3))


def retry(func):
    def wrapper(*args, **kwargs):
        finish = False
        cur = 0
        resp = None
        while not finish and cur < 3:
            cur += 1
            print(cur)
            try:
                resp = func(*args, **kwargs)
                finish = True
            except Exception:
                continue
        if resp is None:
            raise Exception

    return wrapper


def __to_url(uri):
    if uri.startswith('/'):
        return 'https://api.twitter.com' + uri
    else:
        return 'https://api.twitter.com' + '/' + uri


def __get_top_50_followers_ids_by_user_id(user_id):
    resp = session.get(__to_url(f'/2/users/{user_id}/followers'), timeout=TIMEOUT,
                       headers=HEADERS, params={'max_results': 50}).json(encoding='UTF-8')
    if ('errors' in resp.keys()):
        return []
    if resp['meta']['result_count'] == 0:
        return []
    else:
        return list(map(lambda e: e['id'], resp['data']))


def __get_user_id_by_user_name(user_name):
    resp = session.get(__to_url(f'/2/users/by/username/{user_name}'), timeout=TIMEOUT,
                       headers=HEADERS).json(encoding='UTF-8')
    if ('errors' in resp.keys()):
        return '0'
    return resp['data']['id']


def __get_top_5_liked_tweets_by_user_id(user_id):
    time.sleep(2)
    resp = session.get(__to_url(f'/2/users/{user_id}/liked_tweets'), timeout=TIMEOUT, headers=HEADERS,
                       params={'max_results': 5}).json(encoding='UTF-8')
    if ('errors' in resp.keys()):
        return []
    if 'status' in resp.keys() and resp['status'] == '429':
        print('too many requests, please wait 15 mins.')
        exit()
    if resp['meta']['result_count'] == 0:
        return []
    else:
        return list(map(lambda e: e['text'], resp['data']))


@retry
def __check_robot(user_id):
    try:
        result = bom.check_account(user_id)
    except Exception:
        print('botometer error. skip botometer')
        return True
    return float(result['cap']['universal']) > 0.7


if __name__ == '__main__':
    user_name = 'BillGates'
    user_id = __get_user_id_by_user_name(user_name)
    if user_id == '0':
        print('user name not exist')
    else:
        follower_ids = __get_top_50_followers_ids_by_user_id(user_id)
        __check_robot(follower_ids[0])
        user_id_liked_tweets_dict = {}
        for follower_id in tqdm(follower_ids):
            if not __check_robot(follower_id):
                continue
            liked_tweets = __get_top_5_liked_tweets_by_user_id(follower_id)
            if len(liked_tweets) == 0:
                continue
            user_id_liked_tweets_dict[follower_id] = liked_tweets
        json.dump(user_id_liked_tweets_dict,
                  open(f'./{user_name}_user_id_liked_tweets_dict.pkl', 'w+', encoding='utf-8'))
