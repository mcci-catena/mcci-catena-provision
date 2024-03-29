#!/usr/bin/env python3

##############################################################################
# 
# Module: mcci_catena_provision_sigfox.py
#
# Description:
#     Provision a catena device through sigfox API
#
# Copyright notice:
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
import base64
import getpass
import json
import os
import re
import stat
import sys

# Lib imports
import nacl.secret
import nacl.utils
import requests
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
            'KEY': None,
            'DEVEUI': None,
            'DEVID' : None,
            'DEVTYPEID': None,
            'BASENAME' : None,
            'SYSEUI' : None,
            'PAC': None
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
#       Provisioning Functions 
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
    if not "key" in sCommand:
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


def generate_key():
    '''
    To generate secret key for encrypt and decrypt credential

    Args:
        NA

    Returns:
        Key in byte format
    '''
    key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
    return key


def encrypt_credential(key, cred):
    '''
    It encrypts the API access credential 

    Args:
        key: secret key in bytes to encrypt
        cred: api access credential

    Returns:
        Encrypted value
    '''
    box = nacl.secret.SecretBox(key)
    encrypted = box.encrypt(cred)
    return encrypted


def decrypt_credential(key, cred):
    '''
    It decrypts the credential to access API

    Args:
        key: secret key 
        cred: api credential

    Returns:
        Decrypted API credential
    '''
    rkey = key[4:]
    rCred = cred[5:]
    byteKey = bytes.fromhex(rkey)
    byteCred = bytes.fromhex(rCred)
    box = nacl.secret.SecretBox(byteKey)
    decrypted = box.decrypt(byteCred)
    print("Decrypted val: {}".format(decrypted))
    return decrypted.decode()


def get_api_access_info():
    '''
    Get API access information from end user

    Args:
        NA

    Returns:
        Received access info
    '''
    while True:
        loginID = input('Enter API Login Id: ')
        if re.match(r'[0-9a-zA-Z]{24}', loginID):
            loginID = loginID.replace('\n', '')
            break
        else:
            print('Invalid API login id entered')

    while True:
        apiPwd = getpass.getpass('Enter API Password: ')
        if re.match(r'[0-9a-zA-Z]{32}', apiPwd):
            apiPwd = apiPwd.replace('\n', '')
            break
        else:
            print('Invalid API password entered')

    apiAccessInfo = loginID + ":" + apiPwd
    return apiAccessInfo.encode()


def manage_credentials(pDir):
    '''
    To perform credential handling process

    Args:
        pDir: current directory path

    Returns:
        NA
    '''
    secretList = []
    pKey = generate_key()
    apiAccessCred = get_api_access_info()
    encryptCred = encrypt_credential(pKey, apiAccessCred)

    secretList.insert(0, "key=" + pKey.hex() + "\n")
    secretList.insert(1, "cred=" + encryptCred.hex())

    with open('.mcci-catena-provision-sigfox', 'a') as f:
        f.writelines(secretList)

    absPath = os.path.join(pDir, '.mcci-catena-provision-sigfox')
    os.chmod(absPath, stat.S_IRUSR)


def verify_response(stat, resp):
    '''
    Verify the http requests response code 

    Args:
        stat: response code
        resp: response message
    
    Returns: 
        True on success

    '''
    if stat == 200:
        oAppContext.verbose("\nResponse Code: {}\n".format(stat))
    elif stat == 201:
        oAppContext.verbose("\nResponse Code: {}\n".format(stat))
    else:
        oAppContext.verbose("\nResponse Code: {}\n".format(stat))
        oAppContext.verbose("\nResponse: \n{}\n".format(resp))
        oAppContext.fatal("Error: API Requset Failed")

    return True


def get_request(url, header):
    '''
    HTTP GET method requests processed and fetch the results

    Args:
        url: URL to be processed 
        header: HTTP request header

    Returns: 
        HTTP response result 

    '''
    response = requests.get(url, headers=header)

    oAppContext.verbose("\nRequest Header:\n\n{}\n".format(
        response.request.headers)
    )

    responseCode = response.status_code
    result = response.json()
    verify_response(responseCode, result)

    return result


def post_request(url, header, data):
    '''
    HTTP POST method requests processed and fetch the results

    Args:
        url: URL to be processed 
        header: HTTP request header
        data: data to be posted

    Returns: 
        HTTP response result 
    
    '''
    data = json.dumps(data)
    response = requests.post(url, headers=header, data=data)

    oAppContext.verbose("\nRequest Header:\n\n{}\n".format(
        response.request.headers)
    )
    oAppContext.verbose("\nRequest Body:\n\n{}\n".format(
        response.request.body)
    )

    responseCode = response.status_code
    result = response.json()
    verify_response(responseCode, result)

    return result


def generate_auth_credential(cred):
    '''
    To generate the basic auth for http requests

    Args:
        loginId: API login id
        password: API login password

    Returns: 
        It returns basic authentication key

    '''
    encodeCredential = cred.encode('ascii')
    base64EncodeCredential = base64.b64encode(encodeCredential)
    base64DecodeCredential = base64EncodeCredential.decode('ascii')

    return base64DecodeCredential


def get_devicetypeid(dt_url, basic_auth):
    '''
    List the device type id available in sigfox console.

    Args:
        dt_url: device type id url
        basic_auth: Auth key

    Returns: 
        available device type id's

    '''
    reqUrl = dt_url
    auth = basic_auth
    devTypeList = []

    headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': None
    }

    headers['Authorization'] = 'Basic ' + auth

    appResult = get_request(reqUrl, headers)
    oAppContext.verbose("Application Info Result: \n{}\n".format(appResult))

    for dtId in appResult['data']:
        devTypeList.append(dtId['id'])

    return devTypeList


def register_device(dt_url, d_url, basic_auth):
    '''
    Registers device on sigfox backend

    Args:
        dt_url: device type id url
        d_url: device url
        basic_auth: auth key
        dev_info: device post info

    Returns: 
        registered device id

    '''
    
    headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': None
    }

    dCreateDevConfig = {
                'id': None,
                'name': None,
                'prototype': True,
                'deviceTypeId': None,
                'pac': None
    }

    if ((not oAppContext.dVariables['SYSEUI']) or 
        (oAppContext.dVariables['SYSEUI'] == '{SYSEUI-NOT-SET}')):
        while True:
            devEUI = input('Enter Device EUI: ')
            if re.match(r'[0-9A-F]{16}', devEUI):
                oAppContext.dVariables['SYSEUI'] = devEUI.replace('\n', '')
                dCreateDevConfig['EUI'] = devEUI.replace('\n', '')
                oAppContext.dVariables['DEVEUI'] = devEUI.replace('\n', '')
                break
            else:
                print('Invalid device EUI entered.')
    else:
        devEUI = oAppContext.dVariables['SYSEUI']
        # dCreateDevConfig['EUI'] = devEUI.replace('\n', '')
        oAppContext.dVariables['DEVEUI'] = devEUI.replace('\n', '')

    if (not oAppContext.dVariables['DEVID']):
        while True:
            devID = input('Enter Device ID: ')
            if re.match(r'[0-9A-Za-z]{4,}', devID):
                oAppContext.dVariables['DEVID'] = devID.replace('\n', '')
                break
            else:
                print('Invalid device ID entered.')
    else:
        devID = oAppContext.dVariables['DEVID']          

    dCreateDevConfig['id'] = devID
    devName = oAppContext.dVariables['BASENAME']
    devNameExChar = oAppContext.dVariables['DEVID']
    devNameResult = devName + devNameExChar
    dCreateDevConfig['name'] = devNameResult

    getDevTypeIdInfo = get_devicetypeid(dt_url, basic_auth)
    print(getDevTypeIdInfo)

    # DEVTYPEID
    if (not oAppContext.dVariables['DEVTYPEID']):
        while True:
            devTypeID = input('Enter Device ID: ')
            if (re.match(r'[0-9a-f]{24}', devTypeID) and 
                (devTypeID in getDevTypeIdInfo)):
                oAppContext.dVariables['DEVID'] = devTypeID.replace('\n', '')
                break
            else:
                print('Invalid device ID entered.')
    else:
        devTypeID = oAppContext.dVariables['DEVTYPEID']
        if devTypeID not in getDevTypeIdInfo:
            oAppContext.fatal("Invalid DEVTYPEID Received")

    # PAC
    if (not oAppContext.dVariables['PAC']):
        while True:
            pacId = input('Enter PAC Id: ')
            if re.match(r'[0-9A-F]{16}', pacId):
                oAppContext.dVariables['PAC'] = pacId.replace('\n', '')
                break
            else:
                print('Invalid PAC Id entered')
    else:
        pacId = oAppContext.dVariables['PAC']

    dCreateDevConfig['deviceTypeId'] = devTypeID
    dCreateDevConfig['pac'] = pacId
    headers['Authorization'] = 'Basic ' + basic_auth

    pResult = post_request(d_url, headers, dCreateDevConfig)
    oAppContext.debug("Device Created: \n{}\n".format(pResult))
    return pResult


def get_deviceinfo(d_url, basic_auth, device_id):
    '''
    Displays registered device information

    Args:
        d_url: device url
        basic_auth: auth key
        device_id: registered device id

    Returns: 
        registered device information

    '''
    reqUrl = d_url + device_id
    auth = basic_auth

    headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': None
    }

    headers['Authorization'] = 'Basic ' + auth

    appResult = get_request(reqUrl, headers)
    oAppContext.debug("Device Info: \n{}\n".format(appResult))

    return appResult


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
                sResult = writecommand(
                                        (re.sub('\n$', '', line)) + '\n'
                                        )
                if not (type(sResult) is tuple and sResult[0] is None):
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
    deviceTypeUrl = 'https://api.sigfox.com/v2/device-types/'
    deviceUrl = 'https://api.sigfox.com/v2/devices/'

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
        help='Register the device in actility network')
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
        oAppContext.fatal("Baud rate too small: {}"
                                  .format(opt.baudrate)
                                  )
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

    # Check config file
    listDirContent = os.listdir(pDir)
    configFile = [
        True for dirfile in listDirContent if dirfile == '.mcci-catena-provision-sigfox']

    if not configFile:
        manage_credentials(pDir)

    if oAppContext.fRegister:
        with open('.mcci-catena-provision-sigfox', 'r') as f:
            lines = f.readlines()

        readCred = [line.rstrip() for line in lines]

        if len(readCred) != 2:
            path = os.path.join(pDir, '.mcci-catena-provision-sigfox')
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            os.remove('.mcci-catena-provision-sigfox')
            manage_credentials(pDir)

        cred = decrypt_credential(readCred[0], readCred[1])

        authCred = generate_auth_credential(cred)

        devCreationResult = register_device( 
            deviceTypeUrl, 
            deviceUrl, 
            authCred)
        devRefId = devCreationResult['id']
        devInfoResult = get_deviceinfo(deviceUrl, authCred, devRefId)
        oAppContext.dVariables['PAC'] = devInfoResult['pac']

        oAppContext.verbose("Vars Dict:\n {}".format(oAppContext.dVariables))

    if opt.script:
        doscript(opt.script[0])

    cResult = closeport(oAppContext.sPort)
    if not cResult:
        oAppContext.error("Can't close port {}".format(oAppContext.sPort))

    oAppContext.exitchecks()
