#!/usr/bin/env python3

##############################################################################
# 
# Module: mcci_catena_provision_helium.py
#
# Function:
#     Provision a catena device through Helium cli
#
# Copyright and License:
#     This file copyright (c) 2021 by
#
#         MCCI Corporation
#         3520 Krums Corners Road
#         Ithaca, NY  14850
#
#     See accompanying LICENSE file for copyright and license information.
#
# Author:
#     Sivaprakash Veluthambi, MCCI   May 2021
#
##############################################################################

# Built-in imports
import argparse
import os
import re
import subprocess
import sys

# Lib imports
import pexpect
from pexpect import fdpexpect
import serial
from serial.tools import list_ports

class AppContext:
    '''
    Class contains common attributes and default values 

    '''

    def __init__(self):
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
        self.dVariables = {
            'APPEUI': None,
            'DEVEUI': None,
            'APPKEY': None,
            'BASENAME' : None,
            'SYSEUI' : None
        }
        

    def warning(self, msg):
        '''
        Display warning message

        Args:
            msg: receives warning messages

        Returns: 
            No explicit result
                
        '''
                
        self.nWarnings = self.nWarnings + 1

        print (msg, end='\n')
        

    def error(self, msg):
        '''
        Display error message

        Args:
            msg: receives error messages

        Returns: 
            No explicit result
                
        '''
                
        self.nErrors = self.nErrors + 1

        print (msg, end='\n')
        

    def fatal(self, msg):
        '''
        Display error message and exit

        Args: 
            msg: receives error messages

        Returns: 
            No explicit result
                
        '''
                
        self.error(msg)
        sys.exit(1)


    def debug(self, msg):
        '''
        Display debug message

        Args:
            msg: receives debug messages

        Returns: 
            No explicit result
                
        '''
                
        if (self.fDebug):
            print (msg, end='\n')
        

    def verbose(self, msg):
        '''
        Display verbose message

        Args: 
            msg: receives verbose message

        Returns: 
            No explicit result
                
        '''
                
        if (self.fVerbose):
            print (msg, end='\n')
        

    def getnumerrors(self):
        '''
        Get the error count

        Args: 
            NA

        Returns: 
            Number of errors occured
                
        '''
                
        nErrors = self.nErrors

        if (self.fWerror):
            nErrors = nErrors + self.nWarnings

        return nErrors
        

    def exitchecks(self):
        '''
        Display total errors detected

        Args: 
            NA

        Returns: 
            0 if no errors occured or 1 otherwise
                
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
#   Provisioning Functions 
#
##############################################################################

def openport(sPortName):
    '''
    Open serial port

    Args: 
        sPortName: serial port name

    Returns: 
        True if port opens or None otherwise
        
    '''
        
    # Check port is available
    listPort = []
    listPort = list(list_ports.comports())
    portAvail = [p.device for p in listPort if p.device == sPortName]

    if not portAvail:
        oAppContext.error("Port {} is unavailable".format(sPortName))
        return None

    # Open port
    if not comPort.is_open:
        try:
            comPort.open()
            if comPort.is_open:
                oAppContext.debug("Port {} opened".format(sPortName))
                return True
        except Exception as err:
            oAppContext.fatal("Can't open port {0} : {1}".format(
                sPortName, 
                err)
            )
            return None
    else:
        oAppContext.warning("Port {} is already opened".format(sPortName))
        return True


def writecommand(sCommand):
    '''
    Transfer command to catena and receive result.
        
    It sends `sCommand` (followed by a new line) to the port. It then reads
    up to 1k characters until a timeout occurs (which is one second). It
    then tries to parse the normal catena response which ends either with
    "\nOK\n" or "\n?<error>\n"

    Args: 
        sCommand: catena command

    Returns: 
        catena result if success; None and error message if fail.
        
    '''

    oAppContext.debug(">>> {}".format(sCommand))

    if comPort.in_waiting != 0:
        comPort.reset_input_buffer()

    try:
        comPort.write(sCommand.encode())
        oAppContext.verbose("Command sent: {}".format(sCommand))
    except Exception as err:
        oAppContext.error("Can't write command {0} : {1}".format(
            sCommand, 
            err)
        )
        return None

    try:
        result = comPort.read(1024)
        sResult = result.decode()
        comPort.reset_input_buffer()
    except Exception as err:
        oAppContext.error("Can't read command response : {}".format(err))
        return None

    if sResult:
        debugMsg = '<<< ' + sResult.replace('\r', '')
        oAppContext.debug(debugMsg)

    sResult = '\n'.join(sResult.splitlines())
    sResult = sResult + '\n'

    # Parse the results
    d= {'code': 'timed out', 'msg': None}
    sResult = re.search(
        r'^([\s\S]*)^\n([OK]*[\s\S]*)\n$',
        sResult, 
        re.MULTILINE)
        
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

    Args: 
        NA

    Returns: 
        True; None if fails

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

    Args: 
        NA

    Returns: 
        A dict containing the catena version info; None if fails
        
    '''

    sVersionCommand = "system version\n"
    sVersion = writecommand(sVersionCommand)

    if type(sVersion) is tuple and sVersion[0] is None:
        dResult = {'Board': '?', 'Platform-Version': '?'}
        return dResult

    sVersion = re.sub(r'\n', '\n\r', sVersion, re.MULTILINE)
    sVersionWrap = '\r' + sVersion + '\n'
    oAppContext.verbose("sVersionWrap: {}".format(sVersionWrap))
        
    sVersionWrap = re.findall(
        r'\r(\S+): ([ \S]+)\n',
        sVersionWrap,
        re.MULTILINE
        )
    dResult = dict(sVersionWrap)

    if ('Board' in dResult and 'Platform-Version' in dResult):
        return dResult
    else:
        oAppContext.error("Unrecognized version response: {}".format(
            sVersion)
        )
        return None


def getsyseui(fPermissive):
    '''
    Get the system EUI for the attached device.

    The device is queried to get the system EUI, which is returned as a
    16-character hex string.

    Args: 
        fPermissive: boolean value

    Returns: 
        A dict containing the system EUI info; None if error occurs
        
    '''
        
    sEuiCommand = "system configure syseui\n"
    lenEui = 64 / 4
    kLenEuiStr = int(lenEui + (lenEui / 2))

    sEUI = writecommand(sEuiCommand)

    if (type(sEUI) is tuple) and (sEUI[0] is None):
        if not fPermissive:
                oAppContext.error("Error getting syseui: {}".format(sEUI[1]))
        else:
                oAppContext.warning("Error getting syseui: {}".format(
                    sEUI[1])
                )

        return None

    hexmatch = re.match(r'^(([0-9A-Fa-f]{2})-){7}([0-9A-Fa-f]{2})', sEUI)
        
    if (len(sEUI) != kLenEuiStr) or hexmatch is None:
        oAppContext.error("Unrecognized EUI response: {}".format(sEUI))
        return None
    else:
        sEUI = re.sub(r'-', '', sEUI)
        sEUI = sEUI.replace('\n', '')
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

    Args: 
        fPermissive: boolean value

    Returns: 
        A dict containing the information; True if success or False if fails
        
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
                        .format(
                            tVersion['Board'],
                            tVersion['Platform-Version'],
                            sEUI
                            )
                        )

        if oAppContext.fInfo:
            oAppContext.verbose(
                                "\n Catena Type: {0}\
                                \n Platform Version: {1}\n SysEUI: {2}"
                                .format(
                                    tVersion['Board'],
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


def writeheliumcommand(hCmd):
    '''
    Transer helium command and receive result.

    This function sends `hCmd` to the helium cli, then reads the result. It
    checks the return code number, if it is 0 send result or send error
    message otherwise.

    Args: 
        hCmd: helium command

    Returns: 
        helium result if success, None if failure
        
    '''

    heliumcmd = hCmd
    oAppContext.debug("HELIUM COMMAND: {}".format(' '.join(heliumcmd)))

    sResult = subprocess.Popen(
        heliumcmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )
        
    hResult = pexpect.fdpexpect.fdspawn(sResult.stdout.fileno())

    try:
        index = hResult.expect('Enter API key')
        if index == 0:
            flag = 0
            msg = (hResult.before).decode()
            print("Enter API key: ", end="\n")
            opt = input()
            opt = str(opt)
            sResult.stdin.write(opt.encode())
            heliumResult = sResult.communicate()
    except Exception:
        flag = 1
        msg = (hResult.before).decode()
        oAppContext.verbose("HELIUM RESULT:\n {}".format(msg))
        heliumResult = sResult.communicate()

    if (sResult.returncode == 0) and flag == 0:
        return heliumResult[0].decode()
    elif (sResult.returncode == 0) and flag == 1:
        return msg
    else:
        return None


def heliumcomms(**dVarArgs):
    '''
    Send helium cli commands and receives information to config catena

    This function checks for information in dict to send it to helium cli.
    It then sends command and receives registered device info from helium.
    Parse the results and store it in dict to use it later in script lines.

    Args: 
        **dVarArgs: helium config info in dict

    Returns: 
        True if success else None
        
    '''
        
    devInfo = {}
    dAppeui = None
    dDeveui = None
    dAppKey = None

    if ((not dVarArgs['SYSEUI']) or 
        ('SYSEUI-NOT-SET' in dVarArgs['SYSEUI'])):
        while True:
            devEUI = input('Enter Device EUI: ')
            if re.match(r'[0-9A-F]{16}', devEUI):
                oAppContext.dVariables['SYSEUI'] = devEUI
                break
            else:
                print('Invalid device EUI entered.')
        
    if (not dVarArgs['APPEUI']):
        while True:
            appEUI = input('Enter App EUI: ')
            if re.match(r'[0-9A-F]{16}', appEUI):
                oAppContext.dVariables['APPEUI'] = appEUI
                break
            else:
                print('Invalid application EUI entered.')

    if (not dVarArgs['APPKEY']):
        while True:
            appKey = input('Enter App Key: ')
            if re.match(r'[0-9A-F]{32}', appKey):
                oAppContext.dVariables['APPKEY'] = appKey
                break
            else:
                print("Invalid application key entered.")

    if dVarArgs['BASENAME']:
        devBaseName = dVarArgs['BASENAME'].replace('\n', '')
        sysEUI = oAppContext.dVariables['SYSEUI'].lower()
        sysEUI = sysEUI.replace('\n', '')
        devBaseName = devBaseName + sysEUI.lower()
    else:
        oAppContext.fatal("Must specify devcie basename")

    devRegisterCmdList = ['helium-console-cli', 'device', 'create']
    devInfoCmdList = ['helium-console-cli', 'device', 'get']

    devRegisterCmdList.append(oAppContext.dVariables['APPEUI'])
    devRegisterCmdList.append(oAppContext.dVariables['APPKEY'])
    devRegisterCmdList.append(oAppContext.dVariables['SYSEUI'])
    devRegisterCmdList.append(devBaseName)

    devInfoCmdList.append(oAppContext.dVariables['APPEUI'])
    devInfoCmdList.append(oAppContext.dVariables['APPKEY'])
    devInfoCmdList.append(oAppContext.dVariables['SYSEUI'])

    devRegisterResult = writeheliumcommand(devRegisterCmdList)

    if devRegisterResult is not None:
        oAppContext.debug("HELIUM - Device Registered:\n {}".format(
            devRegisterResult)
        )
    else:
        oAppContext.fatal("Device Registration failed")

    devInfoResult = writeheliumcommand(devInfoCmdList)

    if devInfoResult is not None:
        oAppContext.debug("HELIUM - Device Info:\n {}".format(devInfoResult))
    else:
        oAppContext.fatal("Getting Device Info failed")
        
    regMatch = re.search(
        r'([\s\S]*){\n([\s\S]*)}\n', 
        devInfoResult, 
        re.MULTILINE)
        
    if not regMatch.group(2):
        oAppContext.fatal("Error in Device Info")
    else:
        devInfoPacked = regMatch.group(2)
                
    devInfoPacked = re.sub(' {2,}', '', devInfoPacked)

    devInfoUnpack = re.findall(
        r'(\S+): \"(\S+)\"\,\n', 
        devInfoPacked, 
        re.MULTILINE)

    devInfo = dict(devInfoUnpack)

    for k, v in devInfo.items():
        if k.upper() == "APP_EUI":
            dAppeui = v
        if k.upper() == "DEV_EUI":
            dDeveui = v
        if k.upper() == "APP_KEY":
            dAppKey = v

    if not dAppeui:
        oAppContext.fatal("APPEUI is none")
    elif not dDeveui:
        oAppContext.fatal("DEVEUI is none")
    elif not dAppKey:
        oAppContext.fatal("APPKEY is none")
    else:
        oAppContext.debug("APPEUI: {0}\nDEVEUI: {1}\nAPPKEY: {2}\n".format(
            dAppeui, 
            dDeveui, 
            dAppKey)
        )
        
    if ((dAppeui == oAppContext.dVariables['APPEUI']) and 
        (dAppKey == oAppContext.dVariables['APPKEY']) and 
            (dDeveui == oAppContext.dVariables['SYSEUI'])):
        oAppContext.dVariables['DEVEUI'] = dDeveui
        return True
    else:
        return None


def expand(sLine):
    '''
    Perform macro expansion on a line of text

    This function is looking for strings of the form "${name}" in sLine. If
    ${name} was written, and name was found in the dict, name's value is
    used.

    Args: 
        sLine: catena command line from cat file

    Returns: 
        String suitably expanded
        
    '''

    sResult = re.search(r'^([a-z ]+)\$(\{.*\})$', sLine)

    if not sResult:
        return sLine

    if sResult:
        sPrefix = sResult.group(1)

        sWord = re.search(r'\$\{(.*)\}', sLine)
        sName = sWord.group(1)

        if not sName in oAppContext.dVariables:
            oAppContext.error("Unknown macro {}".format(sName))
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

    Args:
        sFileName: script name

    Returns: 
        True for script success, False for failure
        
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
                sResult = writecommand((re.sub('\n$', '', line)) + '\n')
                if not (type(sResult) is tuple and sResult[0] is None):
                    continue
                else:
                    oAppContext.error("Line: {0}\nError: \n{1}".format(
                        line, 
                        sResult[1])
                    )
                    return False
    return True


def closeport(sPortName):
    '''
    Close serial port

    Args: 
        sPortName: serial port name

    Returns: 
        True if closed or None otherwise
        
    '''
        
    if comPort.is_open:
        comPort.reset_input_buffer()
        comPort.reset_output_buffer()
        comPort.close()
        oAppContext.debug('Port {} closed'.format(sPortName))
        return True
    else:
        oAppContext.error('Port {} already closed'.format(sPortName))
        return None


##############################################################################
#
#   main 
#
##############################################################################

if __name__ == '__main__':
        
    pName = os.path.basename(__file__)
    pDir = os.path.dirname(os.path.abspath(__file__))

    oAppContext = AppContext()

    optparser = argparse.ArgumentParser(
        description='MCCI Catena Provisioning')
    optparser.add_argument(
        '-baud',
        action='store',
        nargs='?',
        dest='baudrate',
        type=int,
        help='Specify the baud rate as a number. Default is 115200')
    optparser.add_argument(
        '-port',
        action='store',
        nargs=1,
        dest='portname',
        type=str,
        required=True,
        help='Specify the COM port name. This is system specific')
    optparser.add_argument(
        '-D',
        action='store_true',
        default=False,
        dest='debug',
        help='Operate in debug mode. Causes more output to be produced')
    optparser.add_argument(
        '-info',
        action='store_true',
        default=False,
        dest='info',
        help='Display the Catena info')
    optparser.add_argument(
        '-v',
        action='store_true',
        default=False,
        dest='verbose',
        help='Operate in verbose mode')
    optparser.add_argument(
        '-echo',
        action='store_true',
        default=False,
        dest='echo',
        help='Echo all device operations')
    optparser.add_argument(
        '-V',
        action='append',
        dest='vars',
        help='Specify ttn config info in name=value format')
    optparser.add_argument(
        '-nowrite',
        action='store_false',
        default=True,
        dest='writeEnable',
        help='Disable writes to the device')
    optparser.add_argument(
        '-permissive',
        action='store_true',
        default=False,
        dest='permissive',
        help='Don\'t give up if SYSEUI isn\'t set.')
    optparser.add_argument(
        '-r',
        action='store_true',
        default=False,
        dest='register',
        help='Registers the device in helium network')
    optparser.add_argument(
        '-Werror',
        action='store_true',
        default=False,
        dest='warning',
        help='Warning messages become error messages')
    optparser.add_argument(
        '-s',
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
        oAppContext.fatal("Baud rate too small: {}".format(opt.baudrate))
    elif opt.baudrate and (opt.baudrate > 9600):
        oAppContext.nBaudRate = opt.baudrate

    # Serial port Settings
    comPort = serial.Serial()
    comPort.port = oAppContext.sPort
    comPort.baudrate = oAppContext.nBaudRate
    comPort.bytesize = serial.EIGHTBITS
    comPort.parity = serial.PARITY_NONE
    comPort.stopbits = serial.STOPBITS_ONE
    # comPort.dsrdtr = True
    # comPort.rtscts = True
    comPort.timeout = 1

    # Add validate and split -V args
    if opt.vars:
        varCount = len(opt.vars)
    else:
        varCount = 0

    for i in range(varCount):
        mResult = re.search(r'^([A-Za-z0-9_]+)=(.*)$', opt.vars[i])

        if not mResult:
            oAppContext.fatal("Illegal variable specification: {}".format(
                opt.vars[i])
            )
        else:
            oAppContext.dVariables[mResult.group(1)] = mResult.group(2)
        
    # Copy the boolean params
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

    # Turn off echo, before start provisioning
    setechooff() 
    checkcomms(oAppContext.fPermissive)

    listDirContent = os.listdir(pDir)
    heliumCli = [True for dirfile in listDirContent if dirfile == 'helium-console-cli' or dirfile == 'helium-console-cli.exe']

    if not heliumCli:
        oAppContext.fatal("helium cli not found; add to path: {}".format(
            pDir)
        ) 

    if oAppContext.fRegister:
        heliumcommResult = heliumcomms(**oAppContext.dVariables)
                
        if heliumcommResult:
            oAppContext.debug("Device Created Successfully")
        else:
            oAppContext.fatal("Failed to create device")

        oAppContext.verbose("Vars Dict:\n {}".format(oAppContext.dVariables))

    if opt.script:
        doscript(opt.script[0])

    cResult = closeport(oAppContext.sPort)
    if not cResult:
        oAppContext.error("Can't close port {}".format(oAppContext.sPort))

    oAppContext.exitchecks()
