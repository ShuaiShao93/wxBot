#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *
import sys, os, ConfigParser, json, time


class GFCoaxerBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)

        self.tuling_key = ""
        self.robot_switch = True
        self.robotOn = False
        self.lastSpeak = None
        self.GFid = None

        try:
            cf = ConfigParser.ConfigParser()
            cf.read('conf.ini')
            self.tuling_key = cf.get('main', 'key')
        except Exception:
            sys.exit('failed to load tuling key')
        print 'tuling_key:', self.tuling_key

    def tuling_auto_reply(self, uid, msg):
        if self.tuling_key:
            url = "http://www.tuling123.com/openapi/api"
            user_id = uid.replace('@', '')[:30]
            body = {'key': self.tuling_key, 'info': msg.encode('utf8'), 'userid': user_id}
            r = requests.post(url, data=body)
            respond = json.loads(r.text)
            result = ''
            if respond['code'] == 100000:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            elif respond['code'] == 200000:
                result = respond['url']
            elif respond['code'] == 302000:
                for k in respond['list']:
                    result = result + u"【" + k['source'] + u"】 " +\
                        k['article'] + "\t" + k['detailurl'] + "\n"
            else:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')

            print '    ROBOT:', result
            return result
        else:
            return u"知道啦"

    def handle_msg_all(self, msg):
        #if GF send me something
        if msg['msg_type_id'] == 4 and msg['content']['type'] == 0 and msg['user']['id'] == self.GFid:
            #if robot is not on and timer is None, start the timer
            if not self.robotOn:
                if self.lastSpeak == None:
                    #print "Timer starts!"
                    self.lastSpeak = time.time()
                    return
            #if robot is on, send auto reply
            else:
                reply = self.tuling_auto_reply(msg['user']['id'], msg['content']['data'])
                self.send_msg_by_uid(reply, msg['user']['id'])
        #if I send GF anything, turn off the robot and reset the timer
        elif msg['msg_type_id'] == 1 and msg['user']['name'] == 'self' and msg['to_user_id'] == self.GFid:
            #print "I spoke and reset the timer!"
            if self.robotOn:
                self.robotOn = False
                result = u'邵大帅来啦！我邵小宝先撤啦！'
                self.send_msg_by_uid(result, self.GFid)
                print '    ROBOT:', result
            self.lastSpeak = None
        #if group chat
        elif msg['msg_type_id'] == 3:
            print msg

    #every 5 seconds, check if the time since last speak has been over 1 min
    def schedule(self):
        curTime = time.time()
        if not self.robotOn and not self.lastSpeak == None and curTime - self.lastSpeak >= 60:
            self.robotOn = True
            result = u'邵大帅在忙呢，先让我邵小宝来陪你聊聊呗~'
            self.send_msg_by_uid(result, self.GFid)
            print '    ROBOT:', result
        time.sleep(5)
    #overwrite get_contact to initiate GF's id
    def get_contact(self):
        if WXBot.get_contact(self):
            #initiate GF's userID
            self.GFid = self.get_user_id(u'老婆')
            if not self.GFid:
                sys.exit('GF account not found!')
            else:
                print "GF ID: ", self.GFid
                return True
        else:
            return False

def main():
    bot = GFCoaxerBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.run()


if __name__ == '__main__':
    main()
