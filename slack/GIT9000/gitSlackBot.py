#!/usr/bin/env python
# coding=utf-8
from time import sleep
from datetime import datetime
import os
import ConfigParser
from slackclient import SlackClient

class GitSlackBot(object):

    def __init__(self):
        
        if os.getenv('SLACK_TOKEN') is not None and os.getenv('SLACK_BOT_ID') is not None and os.getenv('ANNOUNCEMENT_CHANNEL_IDS') is not None: 
            #Get Slackbot Settings from Openshift Environment
            self.token = os.getenv('SLACK_TOKEN')
            self.botUserId = os.getenv('SLACK_BOT_ID').lower()
            self.announcementChannels = os.getenv('ANNOUNCEMENT_CHANNEL_IDS').split(",")
        else:
            #Get Slackbot Client Settings from Config File
            config = ConfigParser.ConfigParser()
            config.readfp(open('config.cfg'))
            self.token = config.get('Slack', 'token')
            self.botUserId = config.get('Slack', 'botUserId').lower()
            self.announcementChannels = config.get('Slack', 'announcementChannelIds').split(",")

        self.slack = SlackClient(self.token)
	
    def startSlackbot(self):
        slackConnectionSuccessNotice = False
        connectionStatus = self.slack.rtm_connect()

        if connectionStatus:
            while connectionStatus:
                if slackConnectionSuccessNotice is False:
                    print self.getTime(0) + " -- App Connection to Slack established"
                message = []

                try:
                    message = self.slack.rtm_read()

                except OSError as e:
                    print 'Slack RTM Read Error.'
                    print 'Original Exception Trace'
                    print e
                
                self.handleSlackMessage(message)
                sleep(1)

                slackConnectionSuccessNotice = 1
        else:
            print self.getTime(0) + ' -- App Connection Failure, Retrying in 30 Seconds...'
            
            sleep(30)
            self.startSlackbot()
    
    def slackAnnouncement(self, announcementMessage):
        for channel in self.announcementChannels:
            channel = channel.strip()
            self.postToSlack(channel, announcementMessage)

    def handleSlackMessage(self, message):
        messageLength = len(message)
        if messageLength > 0:
            messageJson = message[0]

            if ('text' in messageJson and 'channel' in messageJson and 'user' in messageJson and 'bot_id' not in messageJson) and not 'username' in messageJson:
                messageChannel = messageJson['channel']
                messageText = messageJson['text'].encode('utf-8').lower()
                messageUserEncoded = messageJson['user'].encode('utf-8').lower()

                if (messageText.find(self.botUserId) > -1) and not messageUserEncoded == self.botUserId or messageChannel == "D7FF10DBK":
                    
                    
                    if messageText.find('man') == 0 or messageText.find('help') > -1:
                        self.postToSlack(messageChannel, "*Here is a Brief E2-D2 Synopsis:*\n")

                        manMessage = "E2-D2 is an EdTech Bot Designed to Help Monitor and Orchestrate "
                        manMessage += "Performance Testing within Elsevier.\n\n"
                        manMessage += "For information on Performance Testing Methodologies see:\n"
                        manMessage += "https://goo.gl/D8Y89T\n\n"
                        manMessage += "*The Following Options are Available:*\n"
                        manMessage += "1. `test limit`\n"
                        manMessage += "       --Returns the test sample limit, in minutes, for each performance test\n"
                        manMessage += "       --Example: @e2-d2 test limit\n"

                        self.postToSlack(messageChannel, manMessage)
                    elif messageText.find('test') > -1 and messageText.find('limit') > -1:
                        self.postToSlack(messageChannel, "60 minutes")
                    else:
                        self.postToSlack(messageChannel, "I am E2-D2, I am here to help monitor and orchestrate performance tests.")


    @classmethod 
    def getTime(cls, index):
        #Full Date, Day, Hours, Minutes and Seconds in a collection
        timeInfo = {
            0: format(datetime.now(), '%a, %d %b %Y %H:%M:%S'),
            1: format(datetime.now(), '%a'),
            2: format(datetime.now(), '%H'),
            3: format(datetime.now(), '%M'),
            4: format(datetime.now(), '%S'),
            5: format(datetime.now(), '%f'),
            6: format(datetime.now(), '%a, %d %b %Y')
        }

        return str(timeInfo[index])

    def postToSlack(self, messageChannel, message):
        sleep(0.5)
        self.slack.api_call(
            'chat.postMessage',
            channel=messageChannel,
            text=message,
            as_user=True
        )

        print ' Message Sent To Channel: ' + messageChannel + ' - ' + message
