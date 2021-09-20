#!/usr/bin/env python3

##############################################################################
# 
# Module: mcci_catena_provision_ttn.py
#
# Function:
#     Provision a catena device through TTN cli
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
#     Sivaprakash Veluthambi, MCCI   Sep 2021
#
##############################################################################

# Built-in imports
import argparse
import ast
import json
import os
import re
import subprocess
import sys

# Lib imports
import serial
from serial.tools import list_ports

class AppContext:
    '''
    class contains common attributes and default values 
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
            'APPID' : None,
            'BASENAME' : None,
            'DEVID': None,
            'FREQPLAN': None,
            'FREQPLANID': None,
            'LORAVER': None,
            'LORAPHYVER': None,
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
        re.MULTILINE)
        
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
            oAppContext.warning("Error getting syseui: {}".format(sEUI[1]))

        return None

    hexmatch = re.match(r'^(([0-9A-Fa-f]{2})-){7}([0-9A-Fa-f]{2})', sEUI)
        
    if (len(sEUI) != kLenEuiStr) or hexmatch is None:
        oAppContext.error("Unrecognized EUI response: {}".format(sEUI))
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
                                sEUI)
                        )

        if oAppContext.fInfo:
            oAppContext.verbose(
                                "\n Catena Type: {0}\
                                \n Platform Version: {1}\n SysEUI: {2}"
                                .format(
                                        tVersion['Board'],
                                        tVersion['Platform-Version'],
                                        sEUI)
                                )

        oAppContext.dVariables['SYSEUI'] = sEUI.upper()
        oAppContext.tVersion = tVersion
        return True
    elif (tVersion is not None) and (sEUI is None):
        oAppContext.fatal("SysEUI not set")
        return False


def writettncommand(tCmd, tPath):
    '''
    Transer ttnctl command and receive result.

    This function sends `tCmd` to the ttnctl cli, then reads the result. It
    checks the return code number, if it is 0 send result or send error
    message otherwise.

    Args: 
        tCmd: ttnctl command
        tPath: ttn cli path

    Returns: 
        ttnctl result if success, None if failure
        
    '''

    oAppContext.debug("TTN COMMAND: {}".format(' '.join(tCmd)))
        
    try:
        sResult = subprocess.Popen(
            tCmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd=tPath
            )
        op, err = sResult.communicate()
    except Exception as e:
        print("Error occured: ", e)
        # sys.exit(1)
        oAppContext.fatal("Subprocess communication failed")

    if sResult.returncode == 1:
        print("Error result in subprocess...")
        oAppContext.debug(op.decode())
        oAppContext.debug(err.decode())
        return False, op.decode()
    else:
        oAppContext.debug(op.decode())
        oAppContext.debug(err.decode())
    
    return True, op.decode()


def checkttnvars():
    '''
    Check and set up required variables for ttn cli command

    Args: 
        NA

    Returns: 
        No explicit result
        
    '''

    # set syseui
    if ((not oAppContext.dVariables['SYSEUI']) or 
        (oAppContext.dVariables['SYSEUI'] == '{SYSEUI-NOT-SET}')):
        while True:
            devEUI = input('Enter Device EUI: ')
            if re.match(r'[0-9A-Fa-f]{16}', devEUI):
                oAppContext.dVariables['SYSEUI'] = devEUI
                break
            else:
                print('Invalid device EUI entered.')
    else:
        oAppContext.dVariables['SYSEUI'] = oAppContext.dVariables['SYSEUI'].replace('\n', '')
    
    # set app id
    if not oAppContext.dVariables['APPID']:
        while True:
            appId = input('Enter Application ID: ')
            if appId:
                oAppContext.dVariables['APPID'] = appId
                break
            else:
                print("Invalid Application Id entered")
    else:
        oAppContext.dVariables['APPID'] = oAppContext.dVariables['APPID'].replace('\n', '')

    # set device base name
    if oAppContext.dVariables['BASENAME']:
        devBaseName = oAppContext.dVariables['BASENAME'].replace('\n', '')
        sysEUI = oAppContext.dVariables['SYSEUI'].lower()
        sysEUI = sysEUI.replace('\n', '')
        devBaseName = devBaseName + sysEUI.lower()
        oAppContext.dVariables['DEVID'] = devBaseName
    else:
        oAppContext.fatal("Must specify device basename")

    # set app eui
    if not oAppContext.dVariables['JOINEUI']:
        while True:
            devEUI = input('Enter Join EUI: ')
            if re.match(r'[0-9A-Fa-f]{16}', devEUI):
                oAppContext.dVariables['JOINEUI'] = devEUI
                break
            else:
                print('Invalid join EUI entered.')
    else:
        oAppContext.dVariables['JOINEUI'] = oAppContext.dVariables['JOINEUI'].replace('\n', '')

    # set lora version
    if not oAppContext.dVariables['LORAVER']:
        oAppContext.dVariables['LORAVER'] = '1.0.3'
    else:
        oAppContext.dVariables['LORAVER'] = oAppContext.dVariables['LORAVER'].replace('\n', '')

    # set region
    if not oAppContext.dVariables['FREQPLAN']:
        oAppContext.dVariables['LORAPHYVER'] = 'PHY_V1_0_3_REV_A'
        oAppContext.dVariables['FREQPLANID'] = 'US_902_928_FSB_2'
    else:
        oAppContext.dVariables['FREQPLAN'] = oAppContext.dVariables['FREQPLAN'].replace('\n', '')

    if oAppContext.dVariables['FREQPLAN'] == 'AS923':
        oAppContext.dVariables['LORAPHYVER'] = 'PHY_V1_0_3_REV_A'
        oAppContext.dVariables['FREQPLANID'] = 'AS_923'
    elif oAppContext.dVariables['FREQPLAN'] == 'AU915':
        oAppContext.dVariables['LORAPHYVER'] = 'PHY_V1_0_3_REV_A'
        oAppContext.dVariables['FREQPLANID'] = 'AU_915_928_FSB_2'
    elif oAppContext.dVariables['FREQPLAN'] == 'EU868':
        oAppContext.dVariables['LORAPHYVER'] = 'PHY_V1_0_3_REV_A'
        oAppContext.dVariables['FREQPLANID'] = 'EU_863_870_TTN'
    elif oAppContext.dVariables['FREQPLAN'] == 'IN866':
        oAppContext.dVariables['LORAPHYVER'] = 'PHY_V1_0_3_REV_A'
        oAppContext.dVariables['FREQPLANID'] = 'IN_865_867'
    elif oAppContext.dVariables['FREQPLAN'] == 'JP923':
        oAppContext.dVariables['LORAPHYVER'] = 'PHY_V1_0_3_REV_A'
        oAppContext.dVariables['FREQPLANID'] = 'AS_920_923_LBT'
    elif oAppContext.dVariables['FREQPLAN'] == 'KR920':
        oAppContext.dVariables['LORAPHYVER'] = 'PHY_V1_0_3_REV_A'
        oAppContext.dVariables['FREQPLANID'] = 'KR_920_923_TTN'
    elif oAppContext.dVariables['FREQPLAN'] == 'US915':
        oAppContext.dVariables['LORAPHYVER'] = 'PHY_V1_0_3_REV_A'
        oAppContext.dVariables['FREQPLANID'] = 'US_902_928_FSB_2'
    else:
        oAppContext.fatal("Invalid frequency region {}".format(oAppContext.dVariables['FREQPLAN']))
    

def createttndevice(tPath):
    '''
    Send ttnctl commands and receives information for config catena

    Args: 
        tPath: ttn cli path

    Returns: 
        Tuple contains bool value and ttn result
        
    '''

    cli = os.path.join(tPath, 'ttn-lw-cli')
    cmdList = [cli, 'end-devices', 'create']
    cmdList.append(oAppContext.dVariables['APPID'])
    cmdList.append(oAppContext.dVariables['DEVID'])
    cmdList.append('--join-eui')
    cmdList.append(oAppContext.dVariables['JOINEUI'])
    cmdList.append('--dev-eui')
    cmdList.append(oAppContext.dVariables['SYSEUI'])

    cmdList.append('--lorawan-version')
    cmdList.append(oAppContext.dVariables['LORAVER'])

    cmdList.append('--lorawan-phy-version')
    cmdList.append(oAppContext.dVariables['LORAPHYVER'])
    cmdList.append('--frequency-plan-id')
    cmdList.append(oAppContext.dVariables['FREQPLANID'])

    cmdList.append('--with-root-keys')

    oAppContext.debug("Creating TTN end device...")
    # oAppContext.debug(' '.join(cmdList))
    result = writettncommand(cmdList, tPath)
    return result


def ttncomms(tPath):
    '''
    This function process the TTN cli communication and stores the result for 
    network provisioning

    Args: 
        tPath: 

    Returns: 
        True on success
        
    '''
    
    # check and set up ttn flags 
    checkttnvars()
    
    devRegResult = createttndevice(tPath)

    if devRegResult[0] and devRegResult[1]:
        oAppContext.verbose(devRegResult[1])
        deviceInfo = json.loads(devRegResult[1])
        oAppContext.dVariables['APPEUI'] = deviceInfo["ids"]["join_eui"]
        oAppContext.dVariables['DEVEUI'] = deviceInfo["ids"]["dev_eui"]
        oAppContext.dVariables['APPKEY'] = deviceInfo["root_keys"]["app_key"]["key"]
    else:
        oAppContext.fatal("TTN end device creation failed")

    return True


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

    oAppContext.verbose("Expansion of {0}: {1}".format(sLine, sResult))
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
                    oAppContext.error("Line: {0}\n Error: \n{1}".format(
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
        help='To register the device in ttn network')
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

    try:
        ttnCliPath = os.environ['TTNLWCLI']
        listDirContent = os.listdir(ttnCliPath)
        ttnctlCli = [True for dirfile in listDirContent if dirfile == 'ttn-lw-cli' or dirfile == 'ttn-lw-cli.exe']
    except Exception as e:
        oAppContext.fatal("ERROR: set ttn-lw-cli env path or check cli available in dir\n {}".format(e))

    if not ttnctlCli:
        oAppContext.fatal("ERROR: ttn-lw-cli not found; add to path: {}".format(pDir)) 

    if oAppContext.fRegister:
        ttncommResult = ttncomms(ttnCliPath)

        if ttncommResult:
            oAppContext.verbose("Vars Dict:\n {}".format(oAppContext.dVariables))

    if opt.script:
        doscript(opt.script[0])

    cResult = closeport(oAppContext.sPort)
    if not cResult:
        oAppContext.error("Can't close port {}".format(oAppContext.sPort))

    oAppContext.exitchecks()
