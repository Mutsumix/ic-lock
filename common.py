import os
import time
import hashlib
import hmac
import base64
import requests
import json
from logging import getLogger, config

env = json.load(open("env/api.env", 'r'))

base_url = env['SwitchBot']['base_url']
token = env['SwitchBot']['token']
secret = env['SwitchBot']['secret']
deviceId = env['SwitchBot']['deviceId']

#ログ設定
# with open('log_config.json', 'r') as f:
log_conf = json.load(open('log_config.json', 'r'))
config.dictConfig(log_conf)
logger = getLogger(__name__)

def make_sign(token: str, secret: str):
    nonce = ''
    t = int(round(time.time() * 1000))
    string_to_sign = bytes(f'{token}{t}{nonce}', 'utf-8')
    secret = bytes(secret, 'utf-8')
    sign = base64.b64encode(
        hmac.new(secret, msg=string_to_sign, digestmod=hashlib.sha256).digest())
    return sign, str(t), nonce


def make_request_header(token: str, secret: str) -> dict:
    sign, t, nonce = make_sign(token, secret)
    headers = {
        "Authorization": token,
        "sign": sign,
        "t": str(t),
        "nonce": nonce
    }
    return headers

def unlock()-> bool:

    headers = make_request_header(token, secret)
    devices_url = base_url + "/v1.1/devices/" + deviceId + "/commands"
    data = {
        "commandType": "command",
        "command": "unlock",
        "parameter": "default",
    }
    try:
        # アンロック
        res = requests.post(devices_url, headers=headers, json=data)
        res.raise_for_status()

    except requests.exceptions.RequestException as e:
        logger.error('response error:', e)
        return False

    return True