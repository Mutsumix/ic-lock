import binascii
import nfc
import os
import json
import urllib.request, json
import requests
import base64
import time
import subprocess
import setproctitle
from pysesame3.auth import WebAPIAuth
from pysesame3.lock import CHSesame2
from logging import getLogger, config

class MyCardReader(object):
    
    RESULT_OK = 0
    RESULT_NG = 1
    RESULT_OTHER = 2
    
    env = json.load(open("env/api.env", 'r'))
        
    #ログ設定
    # with open('log_config.json', 'r') as f:
    log_conf = json.load(open('log_config.json', 'r'))
    config.dictConfig(log_conf)
    logger = getLogger(__name__)
    
    def sound(self, se, count=1):
        subprocess.Popen(['mpg321', '-q', 'SE/' + se + '.mp3'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    def slack(self, result, message):
        url = "https://slack.com/api/chat.postMessage"
        token = self.env['Slack']['token']
        method = "POST"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type" : "application/json; charset=utf-8"
        }

        if result == self.RESULT_OK:
            obj = {                        
                "channel":self.env['Slack']['channel'],
                "text":message+"さんが入室しました"
            }
        elif result == self.RESULT_NG:
            obj = {                        
                "channel":"enter-room-manage",
                "text":message+"さんが入室に失敗しました"
            }
        else:
            obj = {                        
                "channel":"enter-room-manage",
                "text":message
            }

        json_data = json.dumps(obj).encode("utf-8")
        
        request = urllib.request.Request(url, data=json_data, method=method, headers=headers)
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
    
    def open_sesame(self, member) -> bool:
        #SESAME 3
        secret_key = self.env['SESAME']['secret_key']        
        #API key
        api_key = self.env['SESAME']['api_key']
        #SESAME's UUID
        uuid = self.env['SESAME']['uuid']
        
        #Account's api key
        auth = WebAPIAuth(apikey=api_key)
        
        sk_bytes = base64.b64decode(secret_key)
        secret_key_hex = sk_bytes[1:17].hex()
        
        device = CHSesame2(
                authenticator=auth,
                device_uuid=uuid,
                secret_key=secret_key_hex     
        )
        
        #Unlock
        result = device.unlock(history_tag="API by " + member)        
        return result

    def check_sesame(self):
        #SESAME 3
        #API key
        api_key = self.env['SESAME']['api_key']
        #SESAME's UUID
        uuid = self.env['SESAME']['uuid']
        
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
                print(jsonResult["CHSesame2Status"])
        except:
                self.logger.error('【 SESAME API ERROR 】')
                self.slack(self.RESULT_OTHER, 'SESAMEとの通信でエラーが発生しました')
        
    def on_connect(self, tag):
        cardinfo = open("env/cardinfo.env", 'r')
        cardinfo = json.load(cardinfo)
        
        #タッチ時の処理 
        self.logger.info('【 タッチされました 】')

        #タグ情報を全て表示 
        #print(tag)                
        #print(tag.identifier)
        #print(binascii.hexlify(tag.identifier).decode())
        #print(tag.type)

        #IDmのみ取得して表示
        try:
            if tag.type == "Type3Tag":
                self.idm = binascii.hexlify(tag.idm).decode()
                self.logger.info(self.idm + str('Type3Tag'))
                #print("IDm : " + self.idm.decode())
            if tag.type == "Type4Tag":
                self.idm = binascii.hexlify(tag.identifier).decode()
                self.logger.info(self.idm + str('Type4Tag'))

            #特定のIDmだった場合のアクション        
            isMatch = False
            for syain in cardinfo:
                if self.idm == cardinfo[syain]['IDm']:
                    member = cardinfo[syain]['name']
                    self.logger.info('【 ' + member + 'さんのIDがタッチされました 】')
                    self.sound("accept")
                    isMatch = True
                    
                    #Open SESAME logic
                    if (self.open_sesame(member)) == True:
                        #Success
                        self.logger.info(member+"さんが入室しました")
                        self.slack(self.RESULT_OK , member)
                        self.sound("success")
                    else:
                        self.logger.info(member+"さんが入室に失敗しました")
                        self.slack(self.RESULT_NG, member)
                        self.slack("【 解錠に失敗しました。Wi-Fiモジュールの接続を確認して下さい \n  物理鍵を使用するか、管理者に連絡して入室して下さい 】")
                        self.sound("error")
                    break

            if isMatch == False:
                self.logger.info("【 登録のないカードです 】")
                self.sound("error")
                
        except AttributeError:
            print("【 対象外のICカードです 】")
            self.sound("error")
            
        return True
 
    def read_id(self):      
        clf = nfc.ContactlessFrontend('usb:001:011')
        
        try:
            clf.connect(rdwr={'on-connect': self.on_connect})
        finally:   
            clf.close()
 
if __name__ == '__main__':
    
    setproctitle.setproctitle('main-lock')

    cr = MyCardReader()
    
    while True:
        #最初に表示 
        print("タッチ待ちです（入室）")

        #タッチ待ち 
        cr.read_id()
        
        #battery check
         
        #リリース時の処理 
        print("【 タッチが外れました 】")