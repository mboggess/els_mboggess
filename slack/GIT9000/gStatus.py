#!/usr/bin/env python2

from datetime import datetime
from time import sleep
import os
import sys
import multiprocessing
import numpy
import requests
from gitSlackBot import GitSlackBot

lock = multiprocessing.Lock()
gitBot = GitSlackBot()

class GitMonitor(object):
    def __init__(self):
        sleep(1)
        print "Monitoring GIT 9000"
    
    def initializeMonitoring(self):
        global lock, gitBot

        #Init
        self.bot = gitBot
        lock.release()
        

def testMonitoringMapper(targetUrl):
    global lock, gitBot
    lock.acquire()
    gitMonitoringThread = GitMonitor()
    gitMonitoringThread.initializeMonitoring()
   

def botMonitor():
    global gitBot
    print "Starting Bot Messenger..."
    gitBot.startSlackbot()

try:
    print "Setting timezone to GMT-5"
    os.environ['TZ'] = 'EST+05EDT,M4.1.0,M10.5.0'

    #Start Bot Monitoring
    botThread = multiprocessing.Process(target=botMonitor)
    botThread.start()

    #Begin Multi-threading
    botThread.join()

    
except OSError as error:
    print "\nGIT 9000 Monitor Stopped Due to Error"
    print error
