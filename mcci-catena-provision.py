import os
import re
import sys
import serial
import pexpect
import argparse
import subprocess

from pexpect import fdpexpect
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
                                   'DEVEUI': None,
                                   'APPKEY': None,
                                   'APPID' : None,
                                   'BASENAME' : None,
                                   'HANDLERID' : None,
                                   'SYSEUI' : None
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


def writettncommand(tCmd):
        '''
        Transer ttnctl command and receive result.

        This function sends `tCmd` to the ttnctl cli, then reads the result. It
        checks the return code number, if it is 0 send result or send error
        message otherwise.

        :param tCmd: ttnctl command

        :return: ttnctl result if success, None if failure
        
        '''

        ttncmd = tCmd
        oAppContext.debug("TTN COMMAND: {}".format(' '.join(ttncmd)))

        sResult = subprocess.Popen(ttncmd,
                                        stdin = subprocess.PIPE,
                                        stdout = subprocess.PIPE,
                                        stderr = subprocess.PIPE
                                        )
        
        tResult = pexpect.fdpexpect.fdspawn(sResult.stdout.fileno())

        try:
                index = tResult.expect('> ')
                if index == 0:
                        flag = 0
                        msg = (tResult.before).decode()
                        oAppContext.debug("TTNCTL RESULT:\n {}"
                                          .format(msg)
                                          )
                        opt = input()
                        opt = str(opt)
                        sResult.stdin.write(opt.encode())
                        ttnResult, err = sResult.communicate()
        except Exception:
                flag = 1
                msg = (tResult.before).decode()
                oAppContext.verbose("TTNCTL RESULT:\n {}".format(msg))
                ttnResult, err = sResult.communicate()

        if (sResult.returncode == 0) and flag == 0:
                return ttnResult
        elif (sResult.returncode == 0) and flag == 1:
                return msg
        else:
                return None


def ttncomms(**dVarArgs):
        '''
        Send ttnctl commands and receives information to config catena

        This function checks for information in dict to send it to ttnctl cli.
        It then sends command and receives registered device info from ttnctl.
        Parse the results and store it in dict to use it later in script lines.

        :param **dVarArgs: ttnctl config info in dict

        :return: AppEUI, DevEUI, AppKey
        
        '''
        
        devInfo = {}
        dAppeui = None
        dDeveui = None
        dAppKey = None

        if ((not dVarArgs[
                'SYSEUI']) or ('SYSEUI-NOT-SET' in dVarArgs['SYSEUI'])):
                while True:
                        devEUI = input('Enter Device EUI: ')
                        if re.match(r'[0-9A-Fa-f]{16}', devEUI):
                                oAppContext.dVariables['SYSEUI'] = devEUI
                                break
                        else:
                                print('Invalid device EUI entered.')
        
        selectAppCmdList = ['ttnctl', 'applications', 'select']

        if dVarArgs['APPID']:
                dVarArgs['APPID'] = dVarArgs['APPID'].replace('\n', '')
                selectAppCmdList.append(dVarArgs['APPID'])
        else:
                oAppContext.fatal("Must specify APPID")
                
        devRegisterCmdList = ['ttnctl', 'devices', 'register']

        if dVarArgs['BASENAME']:
                devBaseName = dVarArgs['BASENAME'].replace('\n', '')
                sysEUI = oAppContext.dVariables['SYSEUI'].lower()
                sysEUI = sysEUI.replace('\n', '')
                devBaseName = devBaseName + sysEUI.lower()

                devRegisterCmdList.append(devBaseName)
                devRegisterCmdList.append(sysEUI)
        else:
                oAppContext.fatal("Must specify devcie basename")
                
        devInfoCmdList = ['ttnctl', 'devices', 'info']

        if dVarArgs['HANDLERID']:
                dVarArgs['HANDLERID'] = '--handler-id=' + dVarArgs[
                        'HANDLERID'].replace('\n', '')
                devRegisterCmdList.append(dVarArgs['HANDLERID'])
                devInfoCmdList.append(dVarArgs['HANDLERID'])
                
        #devInfoCmdList.append(dVarArgs['APPID'])
        sysEUI = oAppContext.dVariables['SYSEUI']
        sysEUI = sysEUI.replace('\n', '')
        devInfoCmdList.append(
                dVarArgs['BASENAME'] + sysEUI.lower())
        #devInfoCmdList.append('--format')
        #devInfoCmdList.append('string')

        selectAppResult = writettncommand(selectAppCmdList)

        if selectAppResult is not None:
                oAppContext.debug("TTNCTL - Application Selected:\n {}"
                                        .format(selectAppResult)
                                        )
        else:
                oAppContext.fatal("Select Application failed")

        devRegisterResult = writettncommand(devRegisterCmdList)

        if devRegisterResult is not None:
                oAppContext.debug("TTNCTL - Device Registered:\n {}"
                                        .format(devRegisterResult)
                                        )
        else:
                oAppContext.fatal("Device Registration failed")

        devInfoResult = writettncommand(devInfoCmdList)

        if devInfoResult is not None:
                oAppContext.debug("TTNCTL - Device Info:\n {}"
                                        .format(devInfoResult)
                                        )
        else:
                oAppContext.fatal("Getting Device Info failed")

        devInfoResult = re.sub(' {2,}', '', devInfoResult)
        dResult = re.findall(r'^([A-Za-z]+): ([\S ]*)$',
                                devInfoResult,
                                re.MULTILINE
                                )

        devInfo = dict(dResult)

        for k, v in devInfo.items():
                if k.upper() == "APPEUI":
                        dAppeui = v
                if k.upper() == "DEVEUI":
                        dDeveui = v
                if k.upper() == "APPKEY":
                        dAppKey = v

        if not dAppeui:
                oAppContext.fatal("APPEUI is none")
        elif not dDeveui:
                oAppContext.fatal("DEVEUI is none")
        elif not dAppKey:
                oAppContext.fatal("APPKEY is none")
        else:
                oAppContext.debug("APPEUI: {0}\nDEVEUI: {1}\nAPPKEY: {2}\n"
                                        .format(dAppeui, dDeveui, dAppKey)
                                        )
                return dAppeui, dDeveui, dAppKey


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
                               action='append',
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
                               help='To register the device in ttn network')
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
        ttnctlCli = [True for dirfile in listDirContent
                     if dirfile == 'ttnctl' or dirfile == 'ttnctl.exe']

        if not ttnctlCli:
               oAppContext.fatal("ttnctl not found; add to path: {}"
                                 .format(pDir)
                                 ) 

        if oAppContext.fRegister:
                ttncommResult = ttncomms(
                        **oAppContext.dVariables)

                if ttncommResult:
                        oAppContext.dVariables['APPEUI'] = ttncommResult[0] 
                        oAppContext.dVariables['DEVEUI'] = ttncommResult[1]
                        oAppContext.dVariables['APPKEY'] = ttncommResult[2]

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
