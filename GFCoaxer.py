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
        self.robotOn = 0 #0:off 1:auto on 2: force on
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
            #if robot is not on
            if self.robotOn == 0:
                #if the content is calling its name, force on
                if msg['content']['data'] == u'邵小宝':
                    self.robotOn = 2
                    result = "我邵小宝来也~"
                    self.send_msg_by_uid(result, msg['user']['id'])
                    print '    ROBOT:', result
                    self.lastSpeak = None
                #if timer is None, start the timer and record the userID
                elif self.lastSpeak == None:
                    #print "Timer starts!"
                    self.lastSpeak = (time.time(), msg['user']['id'])
            #if robot is on, send auto reply
            else:
                reply = self.tuling_auto_reply(msg['user']['id'], msg['content']['data'])
                self.send_msg_by_uid(reply, msg['user']['id'])
        #if I send GF anything
        elif msg['msg_type_id'] == 1 and msg['user']['name'] == 'self' and msg['to_user_id'] == self.GFid:
            #turn off the robot if it's auto on and reset the timer
            if self.robotOn == 1:
                self.robotOn = 0
                result = u'邵大帅来啦！我邵小宝先撤啦！'
                self.send_msg_by_uid(result, msg['to_user_id'])
                print '    ROBOT:', result
            #if forced on and I told it to quit, it will quit
            elif self.robotOn == 2:
                if msg['content']['data'] == u'小宝去写作业':
                    self.robotOn = 0
                    result = u'邵大帅赶我走啦~拜拜啦'
                    self.send_msg_by_uid(result, msg['to_user_id'])
                    print '    ROBOT:', result
            self.lastSpeak = None
        #if group chat
        elif msg['msg_type_id'] == 3:
            print msg

    #every 5 seconds, check if the time since last speak has been over 1 min
    def schedule(self):
        curTime = time.time()
        if not self.robotOn and not self.lastSpeak == None and curTime - self.lastSpeak[0] >= 60:
            self.robotOn = 1
            result = u'邵大帅在忙呢，先让我邵小宝来陪你聊聊呗~你刚说了啥再说一遍咯'
            self.send_msg_by_uid(result, self.lastSpeak[1])
            print '    ROBOT:', result
        time.sleep(5)
    #overwrite get_contact to initialize GF's id
    def get_contact(self):
        if WXBot.get_contact(self):
            #initialize GF's userID
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
