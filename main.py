import binascii
import nfc
import os
import json
import urllib.request, json
import requests
import base64
import pygame.mixer
import time
from pysesame3.auth import WebAPIAuth
from pysesame3.lock import CHSesame2

class MyCardReader(object):
    
    RESULT_OK = 0
    RESULT_NG = 1
    
    env = json.load(open("env/api.env", 'r'))
    
    def sound(self, se, count=1):
        pygame.mixer.init()
        pygame.mixer.music.load("SE/" + se + ".mp3")
        pygame.mixer.music.play(count)
        time.sleep(10)
        pygame.mixer.music.stop()     
    
    def slack_in(self, result, member):
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
                "text":member+"さんが入室しました"
            }
        else:
            obj = {                        
                "channel":"enter-room-manage",
                "text":member+"さんが入室に失敗しました"
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
        
    def on_connect(self, tag):
        cardinfo = open("env/cardinfo.env", 'r')
        cardinfo = json.load(cardinfo)
        
        #タッチ時の処理 
        print("【 タッチされました 】")

        #タグ情報を全て表示 
        #print(tag)                
        #print(tag.identifier)
        #print(binascii.hexlify(tag.identifier).decode())
        #print(tag.type)

        #IDmのみ取得して表示
        try:
            if tag.type == "Type3Tag":
                self.idm = binascii.hexlify(tag.idm).decode()
                print(self.idm)
                #print("IDm : " + self.idm.decode())
            if tag.type == "Type4Tag":
                self.idm = binascii.hexlify(tag.identifier).decode()
                print(self.idm)

            #特定のIDmだった場合のアクション        
            isMatch = False
            for syain in cardinfo:
                if self.idm == cardinfo[syain]['IDm']:
                    member = cardinfo[syain]['name']
                    print("【 登録されたIDです 】")
                    print("【 " + member + "さん、解錠します 】")
                    self.sound("accept")
                    isMatch = True
                    
                    #Open SESAME logic
                    if (self.open_sesame(member)) == True:
                        #Success
                        self.slack_in(self.RESULT_OK , member)
                        self.sound("success")
                    else:
                        print("【 解錠に失敗しました。Wi-Fiモジュールの接続を確認して下さい \n  物理鍵を使用するか、管理者に連絡して入室して下さい 】")
                        self.slack_in(self.RESULT_NG, member)
                        self.sound("error", 3)
                    
                    break

            if isMatch == False:
                print("【 登録のないカードです 】")
                self.sound("error")
                
        except AttributeError:
            print("【 対象外のICカードです 】")
            self.sound("error")
            
        return True
 
    def read_id(self):
        clf = nfc.ContactlessFrontend('usb')
        try:
            clf.connect(rdwr={'on-connect': self.on_connect})
        finally:
            clf.close()
 
if __name__ == '__main__':
    cr = MyCardReader()
    while True:
        #最初に表示 
        print("タッチしてね")
 
        #タッチ待ち 
        cr.read_id()
        
        #battery check
         
        #リリース時の処理 
        print("【 タッチが外れました 】")