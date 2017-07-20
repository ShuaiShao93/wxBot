#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *
import sys, ConfigParser, json, time


class testBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)

        self.tuling_key = ""
        self.robot_switch = True
        self.robotOn = {} #0:off 1:auto on 2: force on
        self.lastSpeak = {}
        self.GFid = None
        self.talkedID = {}

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
            if msg['user']['id'] not in self.robotOn:
                self.robotOn[msg['user']['id']] = 0
            #if robot is not on
            if self.robotOn[msg['user']['id']] == 0:
                #if the content is calling its name, force on
                if msg['content']['data'] == u'邵小宝':
                    self.robotOn[msg['user']['id']] = 2
                    result = "我邵小宝来也~"
                    self.send_msg_by_uid(result, msg['user']['id'])
                    print '    ROBOT:', result
                    self.lastSpeak[msg['user']['id']] = None
                #if timer is None, start the timer and record the userID
                else:
                    if msg['user']['id'] not in self.lastSpeak:
                        self.lastSpeak[msg['user']['id']] = None
                    if self.lastSpeak[msg['user']['id']] == None:
                        #print "Timer starts!"
                        self.lastSpeak[msg['user']['id']] = time.time()
            #if robot is on, send auto reply
            else:
                reply = self.tuling_auto_reply(msg['user']['id'], msg['content']['data'])
                self.send_msg_by_uid(reply, msg['user']['id'])
        #if I send GF anything
        elif msg['msg_type_id'] == 1 and msg['user']['name'] == 'self' and msg['to_user_id'] in self.lastSpeak:
            self.talkedID[msg['to_user_id']] = time.time()
            if msg['to_user_id'] not in self.robotOn:
                self.robotOn[msg['to_user_id']] = 0
            #turn off the robot if it's auto on and reset the timer
            if self.robotOn[msg['to_user_id']] == 1:
                self.robotOn[msg['to_user_id']] = 0
                result = u'邵大帅来啦！我邵小宝先撤啦！'
                self.send_msg_by_uid(result, msg['to_user_id'])
                print '    ROBOT:', result
            #if forced on and I told it to quit, it will quit
            elif self.robotOn[msg['to_user_id']] == 2:
                if msg['content']['data'] == u'小宝去写作业':
                    self.robotOn[msg['to_user_id']] = 0
                    result = u'邵大帅赶我走啦~拜拜啦'
                    self.send_msg_by_uid(result, msg['to_user_id'])
                    print '    ROBOT:', result
            self.lastSpeak[msg['to_user_id']] = None
        #if group chat
        elif msg['msg_type_id'] == 3:
            pass#print msg

    #every 5 seconds, check if the time since last speak has been over 1 min
    def schedule(self):
        curTime = time.time()
        #check every uid in last Speak if it's over limit time
        for uid in self.lastSpeak:
            if not self.robotOn[uid] and not self.lastSpeak[uid] == None and curTime - self.lastSpeak[uid] >= 60:
                if uid in self.talkedID:
                    print uid, "has been talked and now removed"
                    self.lastSpeak[uid] = None
                    continue
                self.robotOn[uid] = 1
                result = u'邵大帅没看到你的微信，先让我邵小宝来陪你聊聊呗~当然你等他也是可以的啦'
                self.send_msg_by_uid(result, uid)
                print '    ROBOT:', result
        #every 10 min clear talked id set
        for uid in self.talkedID.keys():
            if curTime - self.talkedID[uid] >= 600:
                print uid, "removed from talked list after 10 mins"
                del(self.talkedID[uid])
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
    bot = testBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png' #tty or png
    bot.run()


if __name__ == '__main__':
    main()
