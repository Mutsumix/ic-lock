import binascii
import nfc
import os
import json
import urllib.request, json
import requests

class MyCardReader(object):
    
    def slack_in(self, member):
        url = "https://slack.com/api/chat.postMessage"
        token = ""
        method = "POST"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type" : "application/json; charset=utf-8"
        }
        
        obj = {                        
            "channel":"enter-room-manage",
            "text":member+"さんが入室しました"
        }
        json_data = json.dumps(obj).encode("utf-8")
        
        request = urllib.request.Request(url, data=json_data, method=method, headers=headers)
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
    
    def open_sesame(self):
        device_id = ""
        token = ""
        url = "https://api.candyhouse.co/public/sesame/" + device_id
        method = "POST"
        headers = {
            "Authorization": token,
            "Content-Type" : "application/json; charset=utf-8"
        }
        obj = {                        
            "command":"unlock"
        }        
        json_data = json.dumps(obj).encode("utf-8")
        
        request = urllib.request.Request(url, data=json_data, method=method, headers=headers)
        with urllib.request.urlopen(request) as response:
        #response = urllib.request.urlopen(request)
            response_body = response.read().decode("utf-8")
            print(response_body)
            
    def on_connect(self, tag):
        cardinfo = open("cardinfo.json", 'r')
        cardinfo = json.load(cardinfo)
        
        #タッチ時の処理 
        print("【 タッチされました 】")
 
        #タグ情報を全て表示 
        #print(tag)
 
        #IDmのみ取得して表示
        try:
            self.idm = binascii.hexlify(tag.idm)
            #print("IDm : " + str(self.idm.decode()))

            #特定のIDmだった場合のアクション        
            isMatch = False
            for syain in cardinfo:
                if self.idm.decode() == cardinfo[syain]['IDm']:
                    print("【 登録されたIDです 】")
                    print("【 " + cardinfo[syain]['name'] + "さん、解錠します 】")
                    isMatch = True
                    
                    #Post slack logic
                    self.slack_in(cardinfo[syain]['name'])
                    
                    #Open SESAME logic
                    self.open_sesame()
                    

            if isMatch == False:
                print("【 登録のないカードです 】")
            
        except AttributeError:
            print("【 対象外のICカードです 】")
            
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