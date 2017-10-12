#!/usr/bin/env python
# coding=utf-8
from time import sleep
from datetime import datetime
import os
import ConfigParser
from slackclient import SlackClient
import requests
import re
import sys
from datetime import datetime


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
            self.gitUser = config.get('Git', 'user')
            self.gitUserToken = config.get('Git', 'token')

        self.slack = SlackClient(self.token)
	
    def startSlackbot(self):
        slackConnectionSuccessNotice = False
        connectionStatus = self.slack.rtm_connect()

        if connectionStatus:
            while connectionStatus:
                if slackConnectionSuccessNotice is False:
                    print self.getTime(0) + ' -- App Connection to Slack Established'
                message = []

                try:
                    message = self.slack.rtm_read()

                except OSError as e:
                    print 'Slack RTM Read Error'
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

                if (messageText.find(self.botUserId) > -1) and not messageUserEncoded == self.botUserId or messageChannel == 'D7HJJND3Q':
                    
                    
                    if messageText.find('man') == 0 or messageText.find('help') > -1:
                        self.postToSlack(messageChannel, '*Here is a brief GIT 9000 Synopsis:*\n')

                        manMessage = 'GIT 9000 is an EdTech bot designed to bring certain git workflows '
                        manMessage += "to developers' and managers' fingertips.\n\n"
                        manMessage += '*The following options are available:*\n'
                        manMessage += '- `repos`\n'
                        manMessage += '       --Returns all repos for the elsevierPTG organization\n'
                        manMessage += '       --Example: @git-9000 repos\n'
                        manMessage += '- `branches`\n'
                        manMessage += '       --Returns all branches for the given repo\n'
                        manMessage += '       --Required: `$repo`\n'
                        manMessage += '       --Example: @git-9000 branches eols-outcomes-integration\n'
                        # For `active branches` and `stale branches`, could have optional 'flag' delimiting
                        # time that makes a branch 'active' or 'stale'
                        manMessage += '- `active`\n'
                        manMessage += '       --Returns all active branches for the given repo\n'
                        manMessage += '       --Required: `$repo`\n'
                        manMessage += '       --Example: @git-9000 active branches eols-outcomes-integration\n'
                        manMessage += '- `stale`\n'
                        manMessage += '       --Returns all stale branches for the given repo\n'
                        manMessage += '       --Required: `$repo`\n'
                        manMessage += '       --Example: @git-9000 stale branches eols-outcomes-integration\n'
                        manMessage += '- `tags`\n'
                        manMessage += '       --Returns all tags for the given repo\n'
                        manMessage += '       --Required: `$repo`\n'
                        manMessage += '       --Example: @git-9000 tags eols-outcomes-integration\n'
                        manMessage += '- `diff tags`\n'
                        manMessage += '       NOTE: GitHub API uses tag *names* not the associated commit hash\n'
                        manMessage += '       --Returns a list of commits indicating the changelog between the given tags\n'
                        manMessage += '       --Required: `$repo`, `$tagA` name, and `$tagB` name\n'
                        manMessage += '       --Example: @git-9000 diff tags eols-outcomes-integration v1.0.13 v1.5.3\n'

                        self.postToSlack(messageChannel, manMessage)
                    elif messageText.find('repos') > -1:
                        message = self.getListOfGitItems('repos', '', 'name')
                        self.postToSlack(messageChannel, message)
                    elif messageText.find('branches') > -1 \
                            and messageText.find('active branches') == -1 \
                            and messageText.find('stale branches') == -1:
                        repo = messageText.replace('branches ', '')
                        message = self.getListOfGitItems('branches', repo, 'name')
                        self.postToSlack(messageChannel, message)
                    elif messageText.find('active') > -1:
                        repo = messageText.replace('active branches ', '')
                        branchesList = self.getListOfGitItems('branches', repo, 'name')
                        statusOutput = self.getRepoBranchesStatus(repo, branchesList, 'active')
                        self.postToSlack(messageChannel, statusOutput)
                    elif messageText.find('stale') > -1:
                        repo = messageText.replace('stale branches ', '')
                        branchesList = self.getListOfGitItems('branches', repo, 'name')
                        statusOutput = self.getRepoBranchesStatus(repo, branchesList, 'stale')
                        self.postToSlack(messageChannel, statusOutput)
                    elif messageText.find('diff tags') > -1:
                        repo,tagA,tagB = messageText.replace('diff tags ', '').split()
                        message = self.getGitChangelogBetweenTags(repo, tagA, tagB)
                        self.postToSlack(messageChannel, message)
                    elif messageText.find('tags') > -1:
                        repo = messageText.replace('tags ', '')
                        message = self.getListOfGitItems('tags', repo, 'name')
                        self.postToSlack(messageChannel, message)
                    else:
                        self.postToSlack(messageChannel, 'I am GIT 9000. I am here to facilitate <https://git-scm.com|git> workflows.')


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
            parse='none',
            unfurl_links=False,
            as_user=True
        )

        print ' Message sent to channel: ' + messageChannel + ' - ' + message


    def getNumPages(self, gitURL):
        try:
            r = requests.get(gitURL, auth=(self.gitUser, self.gitUserToken))
        except:
            sys.exit(gitURL + ' is not a valid URL')
        try:
            pages = re.findall('\d+', r.headers['Link'].split('?')[2])[0]
        except:
            pages = 1

        return int(pages)


    def getListOfGitItems(self, itemType, itemName, jsonKey):
        if itemType == 'repos':
            gitURL = 'https://api.github.com/orgs/elsevierPTG/' + itemType
        elif itemType == 'branches':
            gitURL = 'https://api.github.com/repos/elsevierPTG/' + itemName + '/' + itemType
        elif itemType == 'tags':
            gitURL = 'https://api.github.com/repos/elsevierPTG/' + itemName + '/' + itemType
        else:
            sys.exit('Need a new itemType in getListOfGitItems')

        keyList = []
        numPages = self.getNumPages(gitURL)

        for page in range(1, numPages+1):
            try:
                itemDict = requests.get(gitURL + '?page=' + str(page),
                                        auth=(self.gitUser, self.gitUserToken)).json()
            except:
                sys.exit(gitURL + ' is not a valid URL')

            if itemDict['message']:
                message = 'Invalid name: ' + itemName + '.\nPerhaps check your spelling, and try again.\n'
            else:
                itemKeyArray = [x[jsonKey] for x in itemDict]
                for item in range(0, len(itemKeyArray)):
                    keyList.append('`' + itemKeyArray[item] + '`')
                message = self.createMessageFromList(keyList)

        return message


    def getRepoBranchesStatus(self, repo, branchesList, status):
        branchStatusOutput = ''
        # three months in seconds
        active_limit = 7890000

        for branch in branchesList:
            gitURL = 'https://api.github.com/repos/elsevierPTG/' + repo + '/branches/' + branch.replace('`', '')
            try:
                dict = requests.get(gitURL, auth=(self.gitUser, self.gitUserToken)).json()
            except:
                sys.exit(gitURL + ' is not a valid URL')

            lastCommit = dict['commit']['commit']['author']['date']
            diff = int((datetime.now() - datetime.strptime(lastCommit, '%Y-%m-%dT%H:%M:%SZ')).total_seconds())

            if status == 'active' \
                and diff <= active_limit:
                branchStatusOutput += '*Active branches*\n'
                staleCountDown = 90 - (datetime.now() - datetime.strptime(lastCommit, '%Y-%m-%dT%H:%M:%SZ')).days
                branchStatusOutput += branch + ' stale in ' + str(staleCountDown) + ' days\n'
            elif status == 'active' \
                and diff > active_limit:
                continue
            elif status == 'stale' \
                and diff > active_limit:
                branchStatusOutput += '*STALE branches*\n'
                staleCountUp = (datetime.now() - datetime.strptime(lastCommit, '%Y-%m-%dT%H:%M:%SZ')).days - 90
                branchStatusOutput += branch + ' has been STALE for ' + str(staleCountUp) + ' days\n'
            elif status == 'stale' \
                and diff <= active_limit:
                continue
            else:
                sys.exit('Status ' + status + ' or diff ' + str(diff) + \
                         ' missed by check in getRepoBranchesStatus for branch ' + branch)

        if branchStatusOutput == '':
            if status == 'active':
                branchStatusOutput += 'NO active branches for repo `' + repo + '`\n'
            else:
                branchStatusOutput += 'No STALE branches for repo `' + repo + '`\n'

        return branchStatusOutput


    def getGitChangelogBetweenTags(self, repo, tagA, tagB):
        gitURL = 'https://api.github.com/repos/elsevierPTG/' + repo + '/compare/' + tagA + '...' + tagB

        changeLog = []
        numPages = self.getNumPages(gitURL)

        for page in range (1, numPages+1):
            try:
                itemDict = requests.get(gitURL + '?page=' + str(page),
                                        auth=(self.gitUser, self.gitUserToken)).json()
            except:
                sys.exit(gitURL + ' is not a valid URL')

            commitsArray = itemDict['commits']

            for commit in range(0, len(commitsArray)):
                sha = commitsArray[commit]['sha'][0:6]
                message = commitsArray[commit]['commit']['message'].strip('\n')
                changeLog.append('* `' + sha + '` ' + message.replace('\n', ' ') + '\n')

        output = self.createMessageFromList(changeLog)

        return output


    def createMessageFromList(self, list):
        if list != []:
            message = ''
            for item in list:
                message += item + '\n'
            message += 'Number of items: ' + str(len(list))
        else:
            message = 'No items found'
        return message
