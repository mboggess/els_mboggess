#!/usr/bin/env python2

from datetime import datetime
from time import sleep
import os
import sys
import multiprocessing
import numpy
import requests
from performanceSlackBot import PerformanceSlackBot

lock = multiprocessing.Lock()
perfBot = PerformanceSlackBot()

class LocustMonitor(object):
    def __init__(self, targetUrl):
        #Init LocustIO Service Endpoints
        sleep(1)
        print "Monitoring Target URL: " + targetUrl
        self.targetUrl = targetUrl.strip()
    
    def initializeMonitoring(self):
        global lock, perfBot

        #Init
        self.requestsUrl = self.targetUrl + "/stats/requests/csv"
        self.distributionsUrl = self.targetUrl + "/stats/distribution/csv"
        self.statsUrl = self.targetUrl + "/stats/requests"
        self.stopUrl = self.targetUrl + "/stop"
        self.testDataStoragePath = "" 
        self.testSampleLimit = 0
        self.watchNoticeGiven = False
        self.bot = perfBot
        
        #Check for Env Variables and Setup Accordingly
        if os.getenv('TEST_DATA_STORAGE_PATH') is not None:
            self.testDataStoragePath = os.environ['TEST_DATA_STORAGE_PATH']

        if os.getenv('TEST_TIME_LIMIT') is not None  and os.getenv('TEST_TIME_LIMIT').isdigit():
            self.testSampleLimit = os.getenv('TEST_TIME_LIMIT')
        elif len(sys.argv) == 3 and sys.argv[1].isdigit() and int(sys.argv[1]) > 0:
            self.testSampleLimit = sys.argv[1]
        else:
            self.testSampleLimit = 60

        print "Test Limit: " + str(self.testSampleLimit) + " minutes..."

        self.setStoragePath()
        lock.release()
        self.getTestStats()
    
    def getTest(self):
        try:
            locustTest = requests.get(self.statsUrl)
            return locustTest.json()

        except (ValueError, requests.exceptions.ConnectionError) as e:
            offlineJson = {"state": "offline", "errors":[str(e)]}
            return offlineJson
    
    def stopTest(self):
        try:
            requests.get(self.stopUrl)

        except (ValueError, requests.exceptions.ConnectionError):
            print "Failed to stop test"
    
    def downloadRunData(self, testStartTime):
        dataPath = self.testDataStoragePath + 'run-reports/'

        #Create a failure log folder if needed
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)

        r1 = requests.get(self.requestsUrl, stream=True)
        with open(dataPath + str(testStartTime) + 'requests.csv', 'wb') as f:
            for chunk in r1.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)

        r2 = requests.get(self.distributionsUrl, stream=True)
        with open(dataPath + str(testStartTime) + 'distributions.csv', 'wb') as f:
            for chunk in r2.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)

    def setStoragePath(self):

        urlFolderName = self.targetUrl.split('/')[2]

        if os.path.exists(self.testDataStoragePath):
            self.testDataStoragePath = str(self.testDataStoragePath) + "/" + urlFolderName + "/"
        else:
            self.testDataStoragePath = "./" + urlFolderName + "/"

        print "Test Monitoring Storage Path: " + str(self.testDataStoragePath)

    def logErrors(self, testStartTime):
        testKitStatus = self.getTest()['state']
        errorLog = self.getTest()['errors']
        dataPath = self.testDataStoragePath + 'failure-logs/'
        
        #Create a failure log folder if needed
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)

        logHeader = "ErrorText, Method, Count, ServiceEndpoint\n"
        with open(dataPath + str(testStartTime) + 'failures.csv', 'a') as f:
            f.write(logHeader)

        if testKitStatus != "offline":
            for errorLine in errorLog:
                errorText = str(errorLine['error'])
                errorText = errorText.replace(',', '')
                errorMethod = str(errorLine['method'])
                errorCount = str(errorLine['occurences'])
                errorEndpoint = str(errorLine['name'])

                logEntry = errorText + "," + errorMethod + "," + errorCount + "," + errorEndpoint + '\n'

                with open(dataPath + str(testStartTime) + 'failures.csv', 'a') as f:
                    f.write(logEntry)

    def recordServiceVersions(self, testDate):
        dataPath = self.testDataStoragePath + 'test-version-data/'

        #Create a graph results folder if needed
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)

        filename = dataPath + str(testDate) + '-test-versions.txt'

        if os.getenv('PERFBOT_TOKEN') is not None:
            url = 'https://openshift-master.els-ols.com/oapi/v1/namespaces/perf/imagestreams'
            headers = {'Authorization': 'Bearer ' + os.getenv('PERFBOT_TOKEN')}
            response = requests.get(url, headers=headers)

            with open(filename, 'a') as f:

                for item in response.json()['items']:
                    if 'tags' in item['status']:
                        serviceEntry = item['metadata']['name'] + ":" + item['status']['tags'][0]['tag'] + "\n"
                        f.write(serviceEntry)

    def getGridDashboardMap(self):
        if self.targetUrl == "https://locustio2-automation2.apps.els-ols.com":
            return ["Sherpath", "https://insights.newrelic.com/accounts/1060118/dashboards/406269"]
        elif self.targetUrl == "https://locustio3-automation2.apps.els-ols.com":
            return ["HESI ", "https://insights.newrelic.com/accounts/1060118/dashboards/406173"]
        elif self.targetUrl == "https://locustio4-automation2.apps.els-ols.com":
            return ["EAQ", "https://insights.newrelic.com/accounts/1060118/dashboards/406217"]
        elif self.targetUrl == "https://locustio5-automation2.apps.els-ols.com":
            return ["NCO", "https://insights.newrelic.com/accounts/1060118/dashboards/406268"]
        
        return ["Ad-Hoc", self.targetUrl]
    
    def getTestStats(self):
        while True:
            testLoggingActive = False
            rampReached = False
            dataPath = self.testDataStoragePath + 'result-data/'

            if not self.watchNoticeGiven:
                print "Idle Monitor: " + str(self.targetUrl) + "\n"
                self.watchNoticeGiven = True

            locustTest = self.getTest()
            testState = locustTest["state"]
            
            userLoad = 0

            if testState != "offline":
                userLoad = locustTest["user_count"]
            
            testDate = datetime.now().strftime("%m%d%y%H%M")
            testMinuteCount = 0
            testStartTime = testDate

            currentRps = 0
            avgResponse = 0
            numReqs = 0
            avgLength = 0
            failures = 0
            allRPSLevels = []
            allResponseTimes = []
            allFailureRates = []

            while (testState == "running" or testState == "hatching") and (testMinuteCount <= int(self.testSampleLimit) or int(self.testSampleLimit) == 0):

                stats = locustTest["stats"]
                userLoad = int(locustTest["user_count"])
                totalRps = str(locustTest["total_rps"])
                failRatio = str(locustTest['fail_ratio'])
                
                statTotalIndex = len(stats) - 1

                currentRps += stats[statTotalIndex]['current_rps']
                avgResponse += stats[statTotalIndex]['avg_response_time']
                numReqs = str(int(stats[statTotalIndex]['num_requests']) - numReqs)
                avgLength += stats[statTotalIndex]['avg_content_length']
                failures += stats[statTotalIndex]['num_failures']


                logHeader = "TestMinute, UserLoad, CurrentRPS, totalRPS, RequestVolume, AvgResponseTime, AvgContentLength, FailRatio, FailureCount\n"
                logEntry = str(testMinuteCount) + "," + str(userLoad) + "," + str(currentRps) + "," + totalRps + "," + str(numReqs) + "," + str(avgResponse) + "," + str(avgLength) + "," + failRatio + "," + str(failures) + '\n'

                #Create a graph results folder if needed
                if not os.path.exists(dataPath):
                    os.makedirs(dataPath)

                with open(dataPath + str(testDate) + 'locust-testdata.csv', 'a') as f:

                    if testLoggingActive is True:
                        f.write(logEntry)

                        # Record Samples for Analysis - Only RPS after ramp
                        allResponseTimes.append(float(avgResponse))
                        allFailureRates.append(float(failRatio))
                        if testState == "running":
                            allRPSLevels.append(float(currentRps))
                        
                    else:
                        print testDate + " :: Testing Started: " + self.targetUrl 
                        startAnnouncement = ">>>"\
                                            "*Performance Test Started*\n"\
                                            "*Test ID:* " + testDate + "\n"\
                                            "*Environment:* Perf \n"\
                                            "*Test Duration*: " + str(self.testSampleLimit) + " minutes\n"\
                                            "*App Targeted:* " + self.getGridDashboardMap()[0] +"\n"\
                                            "*Monitoring Dashboard:* " + self.getGridDashboardMap()[1] +"\n"

                        self.bot.slackAnnouncement(startAnnouncement)
                        f.write(logHeader)

                testLoggingActive = True

                if testState == "running" and rampReached is False:
                    rampAnnouncement = ">>>"\
                                       "*Performance Test Fully Ramped*\n"\
                                       "*Test ID:* " + testDate + "\n"\
                                       "*App Targeted:* " + self.getGridDashboardMap()[0] +"\n"\
                                       "*Full Load*: " + str(userLoad) + " Threads\n"\
                                       "*Current Avg Response Time*: " + str(round(numpy.average(allResponseTimes), 2)) + " ms\n"\
                                       "*Current Failure Rate*: " + str(round(numpy.average(allFailureRates) * 100, 2)) + "%\n"\
                                       "*Monitoring Dashboard:* " + self.getGridDashboardMap()[1] +"\n"

                    self.bot.slackAnnouncement(rampAnnouncement)
                    rampReached = True

                if testMinuteCount == int(self.testSampleLimit) and int(self.testSampleLimit) != 0:
                    print testDate + " :: Test Limit Hit: " + self.targetUrl
                    self.stopTest()
                
                testMinuteCount += 1

                #Reset Total Stats Per Minute
                currentRps = 0
                avgResponse = 0
                numReqs = 0
                avgLength = 0
                failures = 0

                sleep(60)
                locustTest = self.getTest()
                testState = locustTest["state"]

            if testLoggingActive is True:
                #Turn Logging Off When Stop Detected After Start
                testLoggingActive = False

                #Log test Errors and download Run Data
                self.logErrors(testStartTime)
                self.downloadRunData(testStartTime)
                self.recordServiceVersions(testDate)
                
                stopDate = datetime.now().strftime("%m%d%y%H%M")
                samplesResponse = len(allResponseTimes)
                samplesRPS = len(allRPSLevels)
                samplesFailrate = len(allFailureRates)

                stopAnnouncement = ">>>"\
                                   "*Performance Test Stopped, All Samples Gathered*\n"\
                                   "*Test ID:* " + testDate + "\n"\
                                   "*App Targeted:* " + self.getGridDashboardMap()[0] +"\n"

                if samplesResponse > 0 and samplesRPS > 0 and samplesFailrate > 0:
                    stopAnnouncement += "*Avg Response Time*: " + str(round(numpy.average(allResponseTimes), 2)) + " ms\n"\
                                        "*Avg Load*: " + str(round(numpy.average(allRPSLevels), 2)) + " rps / " + str(round(numpy.average(allRPSLevels) * 60, 2)) + " rpm\n"\
                                        "*Max Load*: " + str(round(numpy.max(allRPSLevels), 2)) + " rps / " + str(round(numpy.max(allRPSLevels) * 60, 2)) + " rpm\n"\
                                        "*Avg Failure Rate*: " + str(round(numpy.average(allFailureRates) * 100, 2)) + "%\n"\

                self.bot.slackAnnouncement(stopAnnouncement)
                print str(testDate) + "-" + str(stopDate) + " :: Test Stopped: " + str(self.targetUrl)

                #Reset Watch Notice for terminal users
                self.watchNoticeGiven = False

            sleep(2)
        

def testMonitoringMapper(targetUrl):
    global lock, perfBot
    lock.acquire()
    locustMonitoringThread = LocustMonitor(targetUrl)
    locustMonitoringThread.initializeMonitoring()
   

def botMonitor():
    global perfBot
    print "Starting Bot Messenger..."
    perfBot.startSlackbot()

try:
    print "Setting timezone to GMT-5"
    os.environ['TZ'] = 'EST+05EDT,M4.1.0,M10.5.0' 
    print "Starting Locust Test Monitor..." 
    urlInput = ""

    if os.getenv('TEST_GRID_URL') is not None:
        print "Test Monitor Set to Openshift Environment Mode"
        urlInput = os.environ['TEST_GRID_URL']
    elif len(sys.argv) == 3 and sys.argv[1].isdigit() and int(sys.argv[1]) > 0:
        print "Test Monitor Set to Command Line Mode"
        urlInput = sys.argv[2]
    else:
        print "Test Monitor Set to Default Mode"
    urlInput = "https://locustio-automation2.apps.els-ols.com"

    #Start Bot Monitoring
    botThread = multiprocessing.Process(target=botMonitor)
    botThread.start()

    #Begin Multi-threading
    testUrls = urlInput.split(',')
    pool = multiprocessing.Pool(len(testUrls)) 
    print str(len(testUrls)) + " Monitoring Processes Starting...\n"
    pool.map(testMonitoringMapper, testUrls)
    pool.join()
    pool.close()
    botThread.join()

    
except OSError as error:
    print "\nLocust Test Monitor Stopped Due to Error"
    print error
    