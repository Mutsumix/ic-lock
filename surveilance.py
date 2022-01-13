import time
import json
import subprocess
import urllib.request, json
from pysesame3.auth import WebAPIAuth
from pysesame3.lock import CHSesame2
from logging import getLogger, config

env = json.load(open("/home/pi/Dev/ic-lock/env/api.env", 'r'))    
#ログ設定
log_conf = json.load(open('/home/pi/Dev/ic-lock/log_config.json', 'r'))
#退出用の出力ファイル名
log_conf["handlers"]["fileHandler"]["filename"] = "/home/pi/Dev/ic-lock/log/surveilance.log"
config.dictConfig(log_conf)
logger = getLogger(__name__)

def slack(message):
        url = "https://slack.com/api/chat.postMessage"
        token = env['Slack']['token']
        method = "POST"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type" : "application/json; charset=utf-8"
        }

        obj = {                        
            "channel":"enter-room-manage",
            "text":message
        }

        json_data = json.dumps(obj).encode("utf-8")
        
        request = urllib.request.Request(url, data=json_data, method=method, headers=headers)
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
            
def check_app_status():
    #LINE token
    token = env['LINE']['token']

    program_list = ["main", "main_out"]

    for program in program_list:
        out = subprocess.Popen(['ps', 'a'], stdout=subprocess.PIPE)
        out = subprocess.Popen(['grep', 'Sl+'], stdin=out.stdout, stdout=subprocess.PIPE)
        out, err = subprocess.Popen(['grep', program + '-lock'], stdin=out.stdout, stdout=subprocess.PIPE).communicate()
        out = out.decode().rstrip()

        if not out:
            #再度タイミングをずらして実行
            out2 = subprocess.Popen(['ps', 'a'], stdout=subprocess.PIPE)
            out2 = subprocess.Popen(['grep', 'Sl+'], stdin=out2.stdout, stdout=subprocess.PIPE)
            out2, err = subprocess.Popen(['grep', program + '-lock'], stdin=out2.stdout, stdout=subprocess.PIPE).communicate()
            out2 = out2.decode().rstrip()

            if not out2:
                subprocess.call(['curl', '-X' ,'POST', 'https://notify-api.line.me/api/notify', '-H', 'Authorization: Bearer ' + token, '-F', 'stickerPackageId=3', '-F', 'stickerId=190', '-F', 'message=スマートロックプログラム' + program + 'が停止中の可能性があります!!' ])
                logger.error(program + ' ERROR')
                slack(program + ' が停止中の可能性があります')
        else:
            logger.info('python program ' + program + ' is OK')

def check_sesame():
    #LINE token
    token = env['LINE']['token']
    #SESAME 3
    #API key
    api_key = env['SESAME']['api_key']
    #SESAME's UUID
    uuid = env['SESAME']['uuid']
    
    url = "https://app.candyhouse.co/api/sesame2/" + uuid
    method = "GET"
    headers = {
        "x-api-key": api_key
    }

    request = urllib.request.Request(url, method=method, headers=headers)

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
            jsonResult = json.loads(response_body)
            logger.info('SESAME 異常なし 状態：' + jsonResult['CHSesame2Status'] + ', 電圧：' + str(jsonResult['batteryPercentage']))
            if jsonResult['batteryPercentage'] < 50:
                slack('SESAMEの電池残量が少なくなっています')
    except:
        logger.error('SESAMEとの通信でエラーが発生しました')
        slack('SESAMEとの通信でエラーが発生しました')
        subprocess.call(['curl', '-X' ,'POST', 'https://notify-api.line.me/api/notify', '-H', 'Authorization: Bearer ' + token, '-F', 'stickerPackageId=3', '-F', 'stickerId=190', '-F', 'message=SESAMEからの反応がありません!!' ])

if __name__=='__main__':
    check_sesame()
    check_app_status()