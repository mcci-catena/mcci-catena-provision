import os
import re
import sys
import json
import serial
import requests
import argparse
import subprocess
import ruamel.yaml

from serial.tools import list_ports

class AppContext:
        '''
        class contains common attributes and default values 
        '''

        def __init__(self):
                '''
                class constructor which has initial default settings

                :param:
                
                '''
                self.nWarnings = 0
                self.nErrors = 0
                self.fVerbose = False
                self.fWerror = False
                self.fDebug = False
                self.sPort = None
                self.nBaudRate = 115200
                self.fWriteEnable = True
                self.fEcho = False
                self.fInfo = False
                self.fPermissive = False
                self.fRegister = False
                self.dVariables = {'APPEUI': None,
                                   'APPKEY': None,
                                   'DEVEUI': None,
                                   'APPKEY': None,
                                   'APPID' : None,
                                   'BASENAME' : None,
                                   'SYSEUI' : None,
                                   'MODEL': None,
                                   'DEVEUI': None,
                                   }
        

        def warning(self, msg):
                '''
                Display warning message

                :param msg: receives warning messages

                :return: No explicit result
                
                '''
                
                self.nWarnings = self.nWarnings + 1

                print (msg, end='\n')
        

        def error(self, msg):
                '''
                Display error message

                :param msg: receives error messages

                :return: No explicit result
                
                '''
                
                self.nErrors = self.nErrors + 1

                print (msg, end='\n')
        

        def fatal(self, msg):
                '''
                Display error message and exit

                :param msg: receives error messages

                :return: No explicit result
                
                '''
                
                self.error(msg)
                sys.exit(1)


        def debug(self, msg):
                '''
                Display debug message

                :param msg: receives debug messages

                :return: No explicit result
                
                '''
                
                if (self.fDebug):
                        print (msg, end='\n')
        

        def verbose(self, msg):
                '''
                Display verbose message

                :param msg: receives verbose message

                :return: No explicit result
                
                '''
                
                if (self.fVerbose):
                        print (msg, end='\n')
        

        def getnumerrors(self):
                '''
                Get the error count

                :Parameters: NA

                :return: Number of errors occured
                
                '''
                
                nErrors = self.nErrors

                if (self.fWerror):
                        nErrors = nErrors + self.nWarnings

                return nErrors
        

        def exitchecks(self):
                '''
                Display total errors detected

                :Parameters: NA

                :return: 0 if no errors occured or 1 otherwise
                
                '''
                
                errCount = self.getnumerrors()
                if (errCount > 0):
                        self.error("{} errors detected".format(errCount))
                        return 1
                else:
                        self.debug("No errors detected")
                        return 0
        

##############################################################################
#
#       Provisioning Functions 
#
##############################################################################

def openport(sPortName):
        '''
        Open serial port

        :param sPortName: serial port name

        :return: True if port opens or None otherwise
        
        '''
        
        #Check port is available
        listPort = []
        listPort = list(list_ports.comports())
        portAvail = [p.device for p in listPort
                        if p.device == sPortName]

        if not portAvail:
                oAppContext.error("Port {} is unavailable"
                                        .format(sPortName)
                                        )
                return None

        #Open port
        if not comPort.is_open:
                try:
                        comPort.open()
                        if comPort.is_open:
                                oAppContext.debug("Port {} opened"
                                                        .format(sPortName)
                                                        )
                                return True
                except Exception as err:
                        oAppContext.fatal("Can't open port {0} : {1}"
                                                .format(sPortName, err)
                                                )
                        return None
        else:
                oAppContext.warning("Port {} is already opened"
                                        .format(sPortName)
                                        )
                return True


def writecommand(sCommand):
        '''
        Transfer command to catena and receive result.
        
        It sends `sCommand` (followed by a new line) to the port. It then reads
        up to 1k characters until a timeout occurs (which is one second). It
        then tries to parse the normal catena response which ends either with
        "\nOK\n" or "\n?<error>\n"

        :param sCommand: catena command

        :return: catena result if success; None and error message if fail.
        
        '''

        oAppContext.debug(">>> {}".format(sCommand))

        if comPort.in_waiting != 0:
                comPort.reset_input_buffer()

        try:
                comPort.write(sCommand.encode())
                oAppContext.verbose("Command sent: {}"
                                        .format(sCommand)
                                        )
        except Exception as err:
                oAppContext.error("Can't write command {0} : {1}"
                                        .format(sCommand, err)
                                        )
                return None

        try:
                result = comPort.read(1024)
                sResult = result.decode()
                comPort.reset_input_buffer()
        except Exception as err:
                oAppContext.error("Can't read command response : {}"
                                        .format(err)
                                        )
                return None

        if sResult:
                debugMsg = '<<< ' + sResult.replace('\r', '')
                oAppContext.debug(debugMsg)

        sResult = '\n'.join(sResult.splitlines())
        sResult = sResult + '\n'

        #parse the results
        d= {'code': 'timed out', 'msg': None}
        sResult = re.search(r'^([\s\S]*)^\n([OK]*[\s\S]*)\n$',
                                sResult, re.MULTILINE)
        
        if sResult:
                d['msg'] = sResult.group(1)
                d['code'] = sResult.group(2)
        else:
                oAppContext.error("Error parsing catena response")

        if 'OK' in d['code']:
                return d['msg']
        else:
                return None, d['code'], d['msg']


def setechooff():
        '''
        To turn off the system echo

        :Parameters: NA

        :return: True; None if fails

        '''
        sEchoOffCommand = "system echo off\n"
        sEcho = writecommand(sEchoOffCommand)

        if type(sEcho) is tuple and sEcho[0] is None:
                oAppContext.fatal("Can't turn off echo: {}".format(sEcho[1]))
        else:
                return True

def getversion():
        '''
        Get the identity of the attached device.

        :Parameters: NA

        :return: A dict containing the catena version info; None if fails
        
        '''

        sVersionCommand = "system version\n"
        sVersion = writecommand(sVersionCommand)

        if type(sVersion) is tuple and sVersion[0] is None:
                dResult = {'Board': '?', 'Platform-Version': '?'}
                return dResult

        sVersion = re.sub(r'\n', '\n\r', sVersion, re.MULTILINE)
        sVersionWrap = '\r' + sVersion + '\n'
        oAppContext.verbose("sVersionWrap: {}".format(sVersionWrap))
        
        sVersionWrap = re.findall(r'\r(\S+): ([ \S]+)\n',
                                        sVersionWrap,
                                        re.MULTILINE
                                        )
        dResult = dict(sVersionWrap)

        if ('Board' in dResult and 'Platform-Version' in dResult):
                return dResult
        else:
                oAppContext.error("Unrecognized version response: {}"
                                        .format(sVersion)
                                        )
                return None


def getsyseui(fPermissive):
        '''
        Get the system EUI for the attached device.

        The device is queried to get the system EUI, which is returned as a
        16-character hex string.

        :Parameters fPermissive: boolean value

        :return: A dict containing the system EUI info; None if error occurs
        
        '''
        
        sEuiCommand = "system configure syseui\n"
        lenEui = 64 / 4
        kLenEuiStr = int(lenEui + (lenEui / 2))

        sEUI = writecommand(sEuiCommand)

        if (type(sEUI) is tuple) and (sEUI[0] is None):
                if not fPermissive:
                        oAppContext.error("Error getting syseui: {}"
                                                .format(sEUI[1])
                                                )
                else:
                        oAppContext.warning("Error getting syseui: {}"
                                                .format(sEUI[1])
                                                )

                return None

        hexmatch = re.match(r'^(([0-9A-Fa-f]{2})-){7}([0-9A-Fa-f]{2})', sEUI)
        
        if (len(sEUI) != kLenEuiStr) or hexmatch is None:
                oAppContext.error("Unrecognized EUI response: {}"
                                        .format(sEUI)
                                        )
                return None
        else:
                sEUI = re.sub(r'-', '', sEUI)
                return sEUI


def checkcomms(fPermissive):
        '''
        Try to recognize the attached device, and verify that comms are
        working.

        The device is queried to get the system EUI, which is returned as a
        16-character hex string, as well as the firmware version.

        ${SYSEUI} (aka oAppContext.dVariables['SYSEUI']) is set to the fetched
        syseui.

        oAppContext.tVersion is set to the fetched version

        :Parameters fPermissive: boolean value

        :return: A dict containing the information; True if success or False if
        fails
        
        '''

        oAppContext.debug("CheckComms")

        tVersion = getversion()

        if tVersion is not None:
                sEUI = getsyseui(fPermissive)
        else:
                sEUI = None

        if (tVersion is not None) and (sEUI is None) and fPermissive:
                sEUI = '{syseui-not-set}'

        if (tVersion is not None) and (sEUI is not None):
                oAppContext.verbose(
                        "\n Catena Type: {0}\
                        \n Platform Version: {1}\n SysEUI: {2}"
                        .format(tVersion['Board'],
                                tVersion['Platform-Version'],
                                sEUI
                                )
                        )

                if oAppContext.fInfo:
                        oAppContext.verbose(
                                "\n Catena Type: {0}\
                                \n Platform Version: {1}\n SysEUI: {2}"
                                .format(tVersion['Board'],
                                        tVersion['Platform-Version'],
                                        sEUI
                                        )
                                )

                oAppContext.dVariables['SYSEUI'] = sEUI.upper()
                oAppContext.tVersion = tVersion
                return True
        elif (tVersion is not None) and (sEUI is None):
                oAppContext.fatal("SysEUI not set")
                return False


def verify_response(rType, stat, resp):
        '''
        It will verify the response of API result whether it is success or not

        :param rType: request type
        :param stat: response code
        :param resp: api result

        :return: True if success

        '''
        requestType = rType
        responseCode = stat
        apiResponse = resp

        if requestType == 'get_token' and responseCode == 200:
                oAppContext.verbose(
                        "\nResponse Code: {}\n".format(responseCode)
                        )
        elif requestType == 'create_device' and responseCode == 201:
                oAppContext.verbose(
                        "\nResponse Code: {}\n".format(responseCode)
                        )
        elif requestType == 'get_req' and responseCode == 200:
                oAppContext.verbose(
                        "\nResponse Code: {}\n".format(responseCode)
                        )
        else:
                oAppContext.verbose(
                        "\nResponse Code: {}\n".format(responseCode)
                        )
                oAppContext.verbose(
                        "\nResponse: \n{}\n".format(apiResponse)
                        )
                oAppContext.fatal("Error: API Requset Failed")

        return True


def get_request(url, header):
        '''
        It will perform GET request

        :param url: request url
        :param header: header information
        
        :return: return API response if success

        '''
        
        gUrl = url
        gHeader = header
        reqType = 'get_req'

        response = requests.get(gUrl, headers=gHeader)

        oAppContext.verbose(
                "\nRequest Header:\n\n{}\n"
                .format(response.request.headers
                ))

        responseCode = response.status_code
        result = response.json()
        verify_response(reqType, responseCode, result)

        return result


def post_request(url, header, data):
        '''
        It will perform POST request

        :param url: request url
        :param header: header information
        :param data: POST data 
        
        :return: return API response if success

        '''

        pUrl = url
        pHeader = header
        pData = data
        reqType = None

        if pHeader['Content-Type'] == 'application/json':
                pData = json.dumps(pData)

        if 'token' in pUrl:
                reqType = 'get_token'

        if 'devices' in pUrl:
                reqType = 'create_device'
        
        response = requests.post(pUrl, headers=pHeader, data=pData)

        oAppContext.verbose(
                "\nRequest Header:\n\n{}\n".format(response.request.headers)
                )
        oAppContext.verbose(
                "\nRequest Body:\n\n{}\n".format(response.request.body)
                )

        responseCode = response.status_code
        result = response.json()
        verify_response(reqType, responseCode, result)

        return result


def get_token(url, tconfiginfo):
        '''
        Get token configuration details and send it to post request for 
        receive token result

        :param url: request url
        :param tconfiginfo: config dict

        :return: token details if success

        '''

        reqUrl = url
        dConfig = tconfiginfo

        headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
        }

        pResult = post_request(reqUrl, headers, dConfig)
        oAppContext.debug("Access Token Generated: \n{}\n".format(pResult))
        return pResult

def get_appinfo(url, token):
        '''
        Send request to receive application information

        :param url: request url
        :param token: access token

        :return: application information if success

        '''

        reqUrl = url
        authToken = token
        appInfo = dict()

        headers = {
                'Accept': 'application/json',
                'Authorization': None
        }

        headers['Authorization'] = authToken

        appResult = get_request(reqUrl, headers)
        oAppContext.verbose("Application Info Result: \n{}\n".format(appResult))

        for i in range(len(appResult)):
                appInfo[appResult[i]['ref']] = appResult[i]['name']
        
        return appInfo


def create_device(dUrl, rUrl, authtoken, dProfId):
        ''' 
        Get device creation information and send post request for create a 
        new device. It also verify the device configuration details before 
        sending post request

        :param dUrl: device creation request url
        :param rUrl: application info request url
        :param authtoken: access token
        :param dProfId: device profile id dict

        :return: created device result if success

        '''

        headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': None
        }

        dCreateDevConfig = {
                'name': None,
                'EUI': None,
                'activationType': 'OTAA',
                'deviceProfileId': None,
                'applicationEUI': None,
                'applicationKey': None
        }

        reqUrl = dUrl
        routeUrl = rUrl
        headers['Authorization'] = authtoken

        if ((not oAppContext.dVariables[
                'SYSEUI']) or 
                (oAppContext.dVariables['SYSEUI'] == 'SYSEUI-NOT-SET')):
                while True:
                        devEUI = input('Enter Device EUI: ')
                        if re.match(r'[0-9A-F]{16}', devEUI):
                                oAppContext.dVariables[
                                        'SYSEUI'] = devEUI.replace('\n', '')
                                dCreateDevConfig[
                                        'EUI'] = devEUI.replace('\n', '')
                                oAppContext.dVariables[
                                        'DEVEUI'] = devEUI.replace('\n', '')
                                break
                        else:
                                print('Invalid device EUI entered.')
        else:
                devEUI = oAppContext.dVariables['SYSEUI']
                dCreateDevConfig['EUI'] = devEUI.replace('\n', '')
                oAppContext.dVariables['DEVEUI'] = devEUI.replace('\n', '')

        devName = oAppContext.dVariables['BASENAME']
        devNameExChar = oAppContext.dVariables['DEVEUI']
        devNameResult = devName + devNameExChar[-4:]
        dCreateDevConfig['name'] = devNameResult

        if (not oAppContext.dVariables['MODEL']):
                for k, v in dProfId.items():
                        for idx, val in enumerate(v):
                                print("{0}. {1}\n".format(idx+1, val))
                
                while True:
                        modIp = input(
                                'Select Device Profile ID (Enter 1 or 2): ')
                        if modIp == 1:
                                oAppContext.dVariables[
                                        'MODEL'] = dProfId[
                                                'profile_id'][modIp-1]
                                dCreateDevConfig[
                                        'deviceProfileId'] = dProfId[
                                                'profile_id'][modIp-1]
                                break
                        elif modIp == 2:
                                oAppContext.dVariables[
                                        'MODEL'] = dProfId[
                                                'profile_id'][modIp-1]
                                dCreateDevConfig[
                                        'deviceProfileId'] = dProfId[
                                                'profile_id'][modIp-1]
                                break
                        else:
                                print('Invalid number entered.')
        else:
                dCreateDevConfig[
                        'deviceProfileId'] = oAppContext.dVariables['MODEL']

        if (not oAppContext.dVariables['APPEUI']):
                while True:
                        appEUI = input('Enter App EUI: ')
                        if re.match(r'[0-9A-F]{16}', appEUI):
                                oAppContext.dVariables['APPEUI'] = appEUI
                                dCreateDevConfig['applicationEUI'] = appEUI
                                break
                        else:
                                print('Invalid application EUI entered.')
        else:
                dCreateDevConfig[
                        'applicationEUI'] = oAppContext.dVariables['APPEUI']

        if (not oAppContext.dVariables['APPKEY']):
                while True:
                        appKey = input('Enter App Key: ')
                        if re.match(r'[0-9A-F]{32}', appKey):
                                oAppContext.dVariables['APPKEY'] = appKey
                                dCreateDevConfig['applicationKey'] = appKey
                                break
                        else:
                                print("Invalid application key entered.")
        else:
                dCreateDevConfig[
                        'applicationKey'] = oAppContext.dVariables['APPKEY']

        if (not oAppContext.dVariables['APPID']):
                appIdResult = get_appinfo(routeUrl, authtoken)
                appIdList = [] 
                
                print("\nAPP ID    APPLICATION NAME")
                print("\n==========================")
                for rId, rName in appIdResult.items():
                        print("\n{}   - {}".format(rId, rName))

                while True:
                        appId = input('\nEnter App ID: ')
                        if re.match(r'[0-9]{5}',appId):
                                appId = str(appId)
                                appIdList.append(appId)
                                oAppContext.dVariables[
                                        'APPID'] = appIdResult[appId]
                                dCreateDevConfig['routeRefs'] = appIdList
                                break
                        else:
                                print("Invalid application id entered.")
        else:
                appIdList = []
                appFlag = 0
                appName = oAppContext.dVariables['APPID']

                appIdResult = get_appinfo(routeUrl, authtoken)

                for rId, rName in appIdResult.items():
                        if (rName == appName):
                                appFlag = 1
                                appId = rId

                if (appFlag == 1):
                        appIdList.append(appId)
                        dCreateDevConfig['routeRefs'] = appIdList
                else:
                        oAppContext.fatal("Invalid APPID Received")

        pResult = post_request(reqUrl, headers, dCreateDevConfig)
        oAppContext.debug("Device Created: \n{}\n".format(pResult))
        return pResult


def get_deviceinfo(url, refId, authtoken):
        '''
        Get device info and send request to receive created device information

        :param url: request url
        :param refId: device reference id
        :param authtoken: access token

        :return: created device information result if success

        '''

        headers = {
                'Accept': 'application/json',
                'Authorization': None
        }

        devId = refId
        reqUrl = url + devId
        headers['Authorization'] = authtoken

        gResult = get_request(reqUrl, headers)
        oAppContext.debug("Device Info: \n{}\n".format(gResult))
        return gResult


def expand(sLine):
        '''
        Perform macro expansion on a line of text

        This function is looking for strings of the form "${name}" in sLine. If
        ${name} was written, and name was found in the dict, name's value is
        used.

        :param sLine: catena command line from cat file

        :return: String suitably expanded
        
        '''

        sResult = re.search(r'^([a-z ]+)\$(\{.*\})$', sLine)

        if not sResult:
                return sLine

        if sResult:
                sPrefix = sResult.group(1)

                sWord = re.search(r'\$\{(.*)\}', sLine)
                sName = sWord.group(1)

                if not sName in oAppContext.dVariables:
                        oAppContext.error("Unknown macro {}"
                                                .format(sName)
                                                )
                        sValue = '{' + sName + '}'
                else:
                        sValue = oAppContext.dVariables[sName]

                sResult = sPrefix + sValue

        oAppContext.verbose("Expansion of {0}: {1}"
                                .format(sLine, sResult)
                                )
        return sResult


def doscript(sFileName):
        '''
        Perform macro expansion on a line of text.

        The file is opened and read line by line.

        Blank lines are ignored. Any text after a '#' character is treated as a
        comment and discarded. Variables of the form ${name} are expanded. Any
        error causes the script to stop.

        :param sFileName: script name

        :return: True for script success, False for failure
        
        '''
        
        oAppContext.debug("DoScript: {}".format(sFileName))

        try:
                with open(sFileName, 'r') as rFile:
                        rFile = rFile.readlines()
        except EnvironmentError as e:
                oAppContext.error("Can't open file: {}".format(e))
                return False

        if not rFile:
                oAppContext.error("Empty file")
                return False

        for line in rFile:
                line = re.sub('\n$', '', line)
                line = re.sub(r'^\s*#.*$', '', line)

                line = expand(line)

                if (re.sub(r'^\s*$', '', line) != ''):
                        if (oAppContext.fEcho):
                                sys.stdout.write(line + '\n')

                        if (oAppContext.fWriteEnable):
                                sResult = writecommand(
                                        (re.sub('\n$', '', line)) + '\n'
                                        )
                                if not (type(sResult) is tuple and 
                                sResult[0] is None):
                                        continue
                                else:
                                        oAppContext.error(
                                                "Line: {0}\n\
                                                Error: \n{1}"
                                                .format(line, sResult[1])
                                                )
                                        return False
        return True


def closeport(sPortName):
        '''
        Close serial port

        :param sPortName: serial port name

        :return: True if closed or None otherwise
        
        '''
        
        if comPort.is_open:
                comPort.reset_input_buffer()
                comPort.reset_output_buffer()
                comPort.close()
                oAppContext.debug('Port {} closed'.format(sPortName))
                return True
        else:
                oAppContext.error('Port {} already closed'
                                        .format(sPortName)
                                        )
                return None


##############################################################################
#
#       main 
#
##############################################################################

if __name__ == '__main__':
        
        pName = os.path.basename(__file__)
        pDir = os.path.dirname(os.path.abspath(__file__))

        oAppContext = AppContext()

        optparser = argparse.ArgumentParser(description
                                            = 'MCCI Catena Provisioning'
                                            )
        optparser.add_argument('-baud',
                               action='store',
                               nargs='?',
                               dest='baudrate',
                               type=int,
                               help='Specify the baud rate as a number. \
                               Default is 115200')
        optparser.add_argument('-port',
                               action='store',
                               nargs=1,
                               dest='portname',
                               type=str,
                               required=True,
                               help='Specify the COM port name. \
                               This is system specific')
        optparser.add_argument('-D',
                               action='store_true',
                               default=False,
                               dest='debug',
                               help='Operate in debug mode. \
                               Causes more output to be produced')
        optparser.add_argument('-info',
                               action='store_true',
                               default=False,
                               dest='info',
                               help='Display the Catena info')
        optparser.add_argument('-v',
                               action='store_true',
                               default=False,
                               dest='verbose',
                               help='Operate in verbose mode')
        optparser.add_argument('-echo',
                               action='store_true',
                               default=False,
                               dest='echo',
                               help='Echo all device operations')
        optparser.add_argument('-V',
                               nargs='+',
                               dest='vars',
                               help='Specify ttn config info in \
                               name=value format')
        optparser.add_argument('-nowrite',
                               action='store_false',
                               default=True,
                               dest='writeEnable',
                               help='Disable writes to the device')
        optparser.add_argument('-permissive',
                               action='store_true',
                               default=False,
                               dest='permissive',
                               help='Don\'t give up if SYSEUI isn\'t set.')
        optparser.add_argument('-r',
                               action='store_true',
                               default=False,
                               dest='register',
                               help='Register the device in actility network')
        optparser.add_argument('-Werror',
                               action='store_true',
                               default=False,
                               dest='warning',
                               help='Warning messages become error messages')
        optparser.add_argument('-s',
                               action='store',
                               nargs=1,
                               dest='script',
                               type=str,
                               help='Specify script name to load catena info')

        opt = optparser.parse_args()

        if not opt.portname:
                oAppContext.fatal("Must specify -port")

        oAppContext.sPort = opt.portname[0]

        if opt.baudrate and (opt.baudrate < 9600):
                oAppContext.fatal("Baud rate too small: {}"
                                  .format(opt.baudrate)
                                  )
        elif opt.baudrate and (opt.baudrate > 9600):
                oAppContext.nBaudRate = opt.baudrate

        #Serial port Settings
        comPort = serial.Serial()
        comPort.port = oAppContext.sPort
        comPort.baudrate = oAppContext.nBaudRate
        comPort.bytesize = serial.EIGHTBITS
        comPort.parity = serial.PARITY_NONE
        comPort.stopbits = serial.STOPBITS_ONE
        #comPort.dsrdtr = True
        #comPort.rtscts = True
        comPort.timeout = 1

        #Add validate and split -V args
        if opt.vars:
                varCount = len(opt.vars)
        else:
                varCount = 0

        for i in range(varCount):
                mResult = re.search(r'^([A-Za-z0-9_]+)=(.*)$', opt.vars[i])

                if not mResult:
                        oAppContext.fatal("Illegal variable specification: {}"
                                          .format(opt.vars[i])
                                          )
                else:
                        oAppContext.dVariables[
                                mResult.group(1)] = mResult.group(2)
        
        # copy the boolean params
        oAppContext.fDebug = opt.debug
        oAppContext.fVerbose = opt.verbose
        oAppContext.fWerror = opt.warning
        oAppContext.fEcho = opt.echo
        oAppContext.fWriteEnable = opt.writeEnable
        oAppContext.fInfo = opt.info
        oAppContext.fPermissive = opt.permissive
        oAppContext.fRegister = opt.register

        hPort = openport(oAppContext.sPort)
        if not hPort:
                sys.exit(1)

        #Turn off echo, before start provisioning
        setechooff() 
        checkcomms(oAppContext.fPermissive)

        listDirContent = os.listdir(pDir)
        configFile = [True for dirfile in listDirContent
                     if dirfile == 'actility-config.yml']

        if not configFile:
               oAppContext.fatal("actility-config.yml not found; \
               add to path: {}"
                                 .format(pDir)
                                 ) 

        if oAppContext.fRegister:
                yaml = ruamel.yaml.YAML()

                with open('actility-config.yml') as yf:
                        yData = yaml.load(yf)

                if yData['request_url']:
                        tokenUrl = yData['request_url']['get_token']
                        deviceUrl = yData['request_url']['device_info']
                        routeUrl = yData['request_url']['get_routes']
                
                if yData['device']:
                        profileIdInfo = dict(yData['device'])

                if (yData['token_generated']['access_token'] is None) or \
                (yData['token_generated']['access_token'] == '<token_value>'):
                        tokenConfigInfo = dict(yData['token_config'])
                        tokenResult = get_token(tokenUrl, tokenConfigInfo)
                        accessToken = tokenResult['access_token']
                        yData['token_generated']['access_token'] = accessToken

                        with open('actility-config.yml', 'w') as wf:
                                yaml.dump(yData, wf)
                else:
                        accessToken = yData['token_generated']['access_token']

                authToken = 'Bearer ' + accessToken

                devCreationResult = create_device(
                        deviceUrl, routeUrl, authToken, profileIdInfo)
                devRefId = devCreationResult['ref']

                devInfoResult = get_deviceinfo(deviceUrl, devRefId, authToken)

                oAppContext.verbose("Vars Dict:\n {}"
                                  .format(oAppContext.dVariables)
                                  )

        if opt.script:
                doscript(opt.script[0])

        cResult = closeport(oAppContext.sPort)
        if not cResult:
               oAppContext.error("Can't close port {}"
                                 .format(oAppContext.sPort)
                                 )

        oAppContext.exitchecks()
