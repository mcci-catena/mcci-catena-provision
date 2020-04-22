# mcci-catena-provision

Set up an MCCI Catena via serial console (USB or regular)

This repository contains two programs.

`mcci-catena-provision.bri` (for Windows only at the moment) loads one or more network provisioning scripts into an MCCI Catena device built using the [Catena-Arduino-Platform](https://github.com/mcci-catena/Catena-Arduino-Platform). It was primarily developed for configuring Catena boards for use with the [The Things Network](https://thethingsnetwork.org). However, the tool can be used for other purposes as desired.

`provision-ttn.sh` provides a streamlined registration flow when working with The Things Network. It registers the device with the network, then uses `mcci-catena-provision` to load the network-generated application credentials into the Catena.

**Contents:**

<!--
  This TOC uses the VS Code markdown TOC extension AlanWalk.markdown-toc.
  We strongly recommend updating using VS Code, the markdown-toc extension and the
  bierner.markdown-preview-github-styles extension. Note that if you are using
  VS Code 1.29 and Markdown TOC 1.5.6, https://github.com/AlanWalk/markdown-toc/issues/65
  applies -- you must change your line-ending to some non-auto value in Settings>
  Text Editor>Files.  `\n` works for me.
-->
<!-- markdownlint-disable MD033 MD004 -->
<!-- markdownlint-capture -->
<!-- markdownlint-disable -->
<!-- TOC depthFrom:2 updateOnSave:true -->

- [mcci-catena-provision](#mcci-catena-provision)
  - [`mcci-catena-provision.bri`](#mcci-catena-provisionbri)
    - [Overview](#overview)
    - [Usage](#usage)
    - [Catena Script File Syntax](#catena-script-file-syntax)
    - [Scripting Reference](#scripting-reference)
    - [Using `catenainit-otaa.cat`](#using-catenainit-otaacat)
  - [`provision-ttn.sh`](#provision-ttnsh)
    - [Usage: `provision-ttn.sh`](#usage-provision-ttnsh)
    - [Environment Variables](#environment-variables)
    - [Example](#example)
  - [`mcci-catena-provision.py`](#mcci-catena-provisionpy)
    - [Required](#required)
    - [Notes](#notes)
    - [Using `mcci-catena-provision.py`](#using-mcci-catena-provisionpy)
    - [Catena Script File](#catena-script-file)
    - [Example (`mcci-catena-provision.py`)](#example-mcci-catena-provisionpy)
  - [`mcci-catena-provision-actility.py`](#mcci-catena-provision-actilitypy)
    - [Required](#required-1)
    - [Notes](#notes-1)
    - [Using `mcci-catena-provision-actility.py`](#using-mcci-catena-provision-actilitypy)
    - [Catena Script File](#catena-script-file-1)
    - [Example (`mcci-catena-provision-actility.py`)](#example-mcci-catena-provision-actilitypy)
  - [`mcci-catena-provision-helium.py`](#mcci-catena-provision-heliumpy)
    - [Required](#required-2)
    - [Notes](#notes-2)
    - [Using `mcci-catena-provision-helium.py`](#using-mcci-catena-provision-heliumpy)
    - [Catena Script File](#catena-script-file-2)
    - [Example (`mcci-catena-provision-helium.py`)](#example-mcci-catena-provision-heliumpy)
  - [Credits](#credits)

<!-- /TOC -->
<!-- markdownlint-restore -->
<!-- Due to a bug in Markdown TOC, the table is formatted incorrectly if tab indentation is set other than 4. Due to another bug, this comment must be *after* the TOC entry. -->

## `mcci-catena-provision.bri`

### Overview

`mcci-catena-provision` reads one or more scripts containing Catena-Arduino-Platform commands, sending each line sequentially to an Catena directly connected to the PC via USB, and checking the results. Simple variable substitution allows you to input provisioning information from the command line, if needed.

Several scripts (`.cat` files, where `cat` is short for "Catena") are provided with the package, to perform common tasks. These include:

* `catenainit-otaa.cat` -- initialize a Catena for LoRa over-the-air authentication ("OTAA"), using information provided from the command line. See "Using `catenainit-otaa.cat`", below.

### Usage

```bash
./bright mcci-catena-provision.bri -[options] [scripts ...]
```

The components of this command may be understood as follows.

`bright mcci-catena-provision.bri` invokes Terry Moore's [Bright interpreter](http://www.lua.org/wshop08.html#moore), which is included (in compiled form) in this package, to run `mcci-catena-provision.bri`. (Sources for Bright are available from Terry, contact author for information; posting to GitHub is pending.)

`-[options]` may be any of the following. Options are processed left to right. Unless we say otherwise, the rightmost option overrides any previous option setting. Boolean options may be negated using the "no" prefix; so for example write "`-noD`" to explicitly negate any previous `-D` option.

* `-baudrate #` sets the desired baud rate. The default is 115200.
* `-D` enables debug output to STDERR.
* `-echo` causes script lines
* `-help` outputs a brief reference, and exits.
* `-info` outputs information about the Catena to STDOUT. This is intended to be used without any script files, in order to get information about the Catena being programmed.
* `-port` _`portname`_ selects the COM port to be used. _`Portname`_ should usually be of the form `com1`, `com2`, etc. You can use Windows Device Manager > Ports (Com & LPT) to get a list of available ports.
* `-V` _name_=_value_ defines a variable named _name_, which can subsequently be used in script files (see "Script File Syntax", below). __This option is cumulative__. You may use it many times to define different variables.
* `-v` selects verbose mode. Additional messages are logged to STDERR.
* `-write` enables writing commands to the Catena. This is the default. `-nowrite` can be used on the command line to cause `mcci-catena-provisions.bri` to go through all the motions (macro expansion, etc.) but not download any data to the Catena. This is intended for use when debugging scripts.
* `-Werror` says that any warning messages should be promoted to errors, resulting in error messages and non-zero exit status.

### Catena Script File Syntax

Catena script files are processed line by line. Blank lines, and lines beginning with whitespace followed by `#` are treated as comments and ignored.

Otherwise the line is macro-expanded and then sent to the Catena.

Macros are indicated using the syntax `${NAME}`, where `NAME` is either a special variable defined by `mcci-catena-provision` or else a variable defined using the `-V` option on the command line. An undefined variable will cause `mcci-load-mode-profile` to report an error.

The special variable `SYSEUI` is always set to the system EUI read from the Catena during initialization.

### Scripting Reference

The scripting commands are defined by the Catena Arduino Platform -- see this [command summary](https://github.com/mcci-catena/Catena-Arduino-Platform#command-summary).

### Using `catenainit-otaa.cat`

The OTAA script `catenainit-otaa.cat` expects that you will invoke `mcci-catena-provision.bri` with the following `-V` definitions:

* `-V APPEUI=0123456789abcdef` -- this is 16-digit application EUI in hex, as displayed by `ttnctl` when you register your device. (Don't worry about byte reversal issues.)
* `-V APPKEY=0123456789abcdef0123456789abcdef` -- this is the 32-digit application key assigned to your device by `ttnctl` when you register your device.

A simple workflow is:

1. Connect your Catena to your PC with a USB cable.
2. Get your device's EUI using `mcci-catena-provision.bri` and the `-info` option.
3. Use that dev EUI to register your device using the TTN console, or the command line tool `ttnctl` [(available here)](https://www.thethingsnetwork.org/docs/network/cli/quick-start.html).
4. Run `mcci-catena-provision.bri` again with the `catenainit-otaa.cat` script, specifying the AppEUI and the AppKey obtained in step 3.

This workflow is automated by [`provision-ttnsh`](#provision-ttnsh), described below.

Here's an example of manual provisioning.

```console
$ # get info about the Catena on port com11.
$ ./bright mcci-catena-provision.bri -port com11 -info
CatenaType: Catena 4630
Platform Version: 0.16.0.1
SysEUI: 0002CC0B001A2B50

$ # check ttnctl version
$ ttnctl version
  INFO Got build information                    Branch=master BuildDate=2019-05-21T08:12:24Z Commit=60b8cc50487095cce789df3c2dcc260e07307f10 Version=v2.10.2-dev
  INFO This is an up-to-date ttnctl build

$ # register the device with the network.
$ ttnctl devices register device-0002CC0B001A2B50 0002CC0B001A2B50
  INFO Using Application                        AppEUI=70B3D57ED000F563 AppID=test-do-not-use
  INFO Generating random AppKey...
  INFO Discovering Handler...                   Handler=ttn-handler-us-west
  INFO Connecting with Handler...               Handler=us-west.thethings.network:1904
  INFO Registered device                        AppEUI=70B3D57ED000F563 AppID=test-do-not-use AppKey=0123456789ABCDEF0123456789ABCDEF DevEUI=0002CC0B001A2B50 DevID=device-0002cc0b001a2b50

# # get the device information
$ ttnctl devices info device-0002cc0b001a2b50
  INFO Using Application                        AppEUI=70B3D57ED000F563 AppID=test-do-not-use
  INFO Discovering Handler...                   Handler=ttn-handler-us-west
  INFO Connecting with Handler...               Handler=us-west.thethings.network:1904
  INFO Found device

  Application ID: test-do-not-use
       Device ID: device-0002cc0b001a2b50
       Last Seen: never

    LoRaWAN Info:

     AppEUI: 70B3D57ED000F563
     DevEUI: 0002CC0B001A2B50
    DevAddr: <nil>
     AppKey: 0123456789ABCDEF0123456789ABCDEF
    AppSKey: <nil>
    NwkSKey: <nil>
     FCntUp: 0
   FCntDown: 0
    Options: FCntCheckEnabled, 32BitFCnt

$ # put the networking info into the device.
$ # ----> be sure to scroll right in the text box to get the entire command that follows:
$ ./bright mcci-catena-provision.bri -port com11 -echo -V APPEUI=0002CC0B001A2B50 -V APPKEY=0123456789ABCDEF0123456789ABCDEF catenainit-otaa.cat
lorawan configure deveui 0002CC0B001A2B50
lorawan configure appeui 70B3D57ED0000852
lorawan configure appkey 0123456789ABCDEF0123456789ABCDEF
lorawan configure fcntup 0
lorawan configure fcntdown 0
lorawan configure devaddr 0
lorawan configure join 1

$
```

## `provision-ttn.sh`

This script uses [`ttnctl`](https://www.thethingsnetwork.org/docs/network/cli/quick-start.html), the API tool for The Things Network, to automatically register a device.

### Usage: `provision-ttn.sh`

```bash
provision-ttn.sh -[options] deveui
```

`-[options]` may be any of the following. Options are processed left to right. Unless we say otherwise, the rightmost option overrides any previous option setting. Boolean options may be negated using the "n" prefix; so for example write "`-nD`" to explicitly negate any previous `-D` option.

* `-a {appid}` selects `{appid}` as the target application ID. If not specified, or if `-a -` is written, then the currently-selected `ttnctl` application is used.
* `-b {basename}` sets the base name for the device. This is similar to the mass registration option in the TTN consol.
* `-D` requests debug output.
* `-h {handler}` specifies the TTN handler associated with this application. The default is `ttn-handler-us-west`.
* `-p {port}` specifies the com port for the Catena. On Windows, this must include the `com` prefix.
* `-s {script}` specifies the `mcci-catena-provision` script to be used for loading the information into the Catena.
* `-v` requests verbose logging.

### Environment Variables

`TTNCTL`, if set, gives the full pathname of the `ttnctl` executable image. If `TTNCTL` is not set, `ttnctl` must be available on the current PATH.

### Example

```console
$ ./provision-ttn.sh  -b iseechange- -a iseechange-01 -s catena-4618-otaa.cat -v -p com20 0002cc0100000346
CatenaType: Catena 4618
Platform Version: 0.16.0.1
SysEUI: 0002CC0100000346
  INFO Found one EUI "70B3D57ED0011966", selecting that one.
  INFO Updated configuration                    AppEUI=70B3D57ED0011966 AppID=iseechange-01
  INFO Using Application                        AppEUI=70B3D57ED0011966 AppID=iseechange-01
  INFO Generating random AppKey...
  INFO Discovering Handler...                   Handler=ttn-handler-us-west
  INFO Connecting with Handler...               Handler=us-west.thethings.network:1904
  INFO Registered device                        AppEUI=70B3D57ED0011966 AppID=iseechange-01 AppKey={redacted} DevEUI=0002CC0100000346 DevID
m=iseechange-0002cc0100000346
provision-from-ttnctl.sh: provisioning Catena
./mcci-catena-provision.bri:
  CatenaType: Catena 4618
  Platform Version: 0.16.0.1
  SysEUI: 0002CC0100000346
system configure syseui 0002CC0100000346
system configure platformguid b75ed77b-b06e-4b26-a968-9c15f222dfb2
lorawan configure deveui 0002CC0100000346
lorawan configure appeui 70B3D57ED0011966
lorawan configure appkey {redacted}
lorawan configure devaddr 0
lorawan configure fcntup 0
lorawan configure fcntdown 0
lorawan configure appskey 0
lorawan configure nwkskey 0
lorawan configure join 1
system configure operatingflags 1
./mcci-catena-provision.bri: No errors detected
```

## `mcci-catena-provision.py`

This script communicates with catena to get information for register it in TTN network via ttnctl cli, then it loads the catena script to device for complete the provisioning process.

### Required

* Python 3.* (Installation steps [here](https://realpython.com/installing-python/))
* Install Python packages [pyserial](https://pyserial.readthedocs.io/en/latest/pyserial.html#installation) and [pexpect](https://pexpect.readthedocs.io/en/stable/install.html) using following commands in terminal/command prompt:
  1. `pip install pyserial`
  2. `pip install pexpect`
* The Things Network CLI. Download it [here](https://www.thethingsnetwork.org/docs/network/cli/quick-start.html)
* Catena Script File (It should be placed in the same repository as the script)

### Notes

1. You need to chose a directory for this script and supporting materials.
If you use `git clone`, you'll specify the target directory; if you download
the zip file from git, then you'll need to choose a place to unpack the
files.

2. Once the files are unpacked, you'll also need to get some additional
files, in particular `ttnctl`. You can put this on your executable path, but
the easiest thing is to put it in the same directory as the script.

3. When you get ttnctl, it will have a very long name specific  to your
operating system (like `ttnctl-windows-amd64.exe` on 64-bit Windows). Copy
or rename the file to `ttnctl.exe` (on Windows) or `ttnctl` (on macOS and
Linux).

4. You'll need to log in to the TTN console using `ttnctl user login
[ttnctl access code]`. Get the access code from [account.thethingsnetwork.org](https://account.thethingsnetwork.org/)

### Using `mcci-catena-provision.py`

```bash
python mcci-catena-provision.py -[options]
```

`-[options]` may be any of the following:

* `-D` - enables debug output.
* `-port` - selects the COM port to be used. For Example: `-port COM11` (windows) or `-port /dev/tty*` (linux) or `-port /dev/cu.*` (Mac)
* `-baud` - sets the desired baud rate. The default is 115200.
* `-info` - outputs information about the Catena to STDOUT.
* `-v` - selects verbose mode.
* `-V` - name=value defines a variable named name, which can subsequently be used in ttnctl application configuration. This option is cumulative. You may use it many times to define different variables. For example, `-V APPID=mycatena4450 BASENAME=mycatena4450- HANDLERID=ttn-handler-eu`
* `-echo` - causes script lines.
* `-nowrite` - disable writing commands from script file to the Catena.
* `-s` - specifies the mcci-catena-provision script to be used for loading the information into the Catena.
* `-Werror` - says that any warning messages should be promoted to errors, resulting in error messages and non-zero exit status.

### Catena Script File

A number of provisioning scripts are provided for setting up Catenas; the
files are named as `{script}.cat`. If your Catena has already been set up at
the factory, you can use `catena-otaa.cat`.  Here are the scripts by name
and function:

* `catenainit-otaa.cat` - Configure a Catena for OTAA
* `catena-4610-base-otaa.cat` - Configure a Catena 4610 in production
* `catena-4617-otaa.cat` - Configure a Catena 4617 in production
* `catena-4618-otaa.cat` - Configure a Catena 4618 in production
* `catena-4630-otaa.cat` - Configure a Catena 4630 in production

The scripts conventionally get information from variables that are set up
by you or by the script. The variables are:

* `APPID` - The TTN application ID (the name, not the application key).
The script uses this to register the device and to obtain the keys.
* `BASENAME` - The base name to be used for devices. This must be a legal
DNS-like name (letters, digits and dashes). The device EUI is appended to
the name. If you want a dash as a separator between the basename and the
DEVEUI, you must end the basename value with a dash.
* `HANDLERID` - The TTN handler to be used for the device. It's very
important to use the appropriate handler for the region where the device is
to be deployed. Values can be found on TTN console. As of this writing, the
valid handler values were "ttn-handler-eu" and  "ttn-handler-us-west".
* `APPEUI` - The Application EUI is a unique 64 bit identifier for the application on the network.
* `DEVEUI` - The device EUI is a unique 64 bit identifier for the end-device on the network.
* `APPKEY` - The App key is a unique 128 bit identifier which used to secure the communication between the device and the network. It is only known by the device and by the application.

### Example (`mcci-catena-provision.py`)

```console
python3 mcci-catena-provision.py -D -port /dev/cu.usbmodem621 -V APPID=myloracat-test BASENAME=myloracat-test- HANDLERID=ttn-handler-eu -s catenainit-otaa.cat

Port /dev/cu.usbmodem621 opened
CheckComms
>>> system version

<<< Board: Catena 4450
Platform-Version: 0.17.0
Arduino-LoRaWAN-Version: 0.6.0
Arduino-LMIC-Version: 2.3.2.51
MCCIADK-Version: 0.2.1
OK

>>> system configure syseui

<<< 00-02-cc-01-00-00-00-7d
OK

TTN COMMAND: ttnctl applications select myloracat-test
TTNCTL - Application Selected:
  INFO Found one EUI "70B3D57ED0020B11", selecting that one.
  INFO Updated configuration                    AppEUI=70B3D57ED0020B11 AppID=myloracat-test

TTN COMMAND: ttnctl devices register myloracat-test-0002cc010000007d 0002cc010000007d --handler-id=ttn-handler-eu
TTNCTL - Device Registered:
  INFO Using Application                        AppEUI=70B3D57ED0020B11 AppID=myloracat-test
  INFO Generating random AppKey...
  INFO Discovering Handler...                   Handler=ttn-handler-eu
  INFO Connecting with Handler...               Handler=eu.thethings.network:1904
  INFO Registered device                        AppEUI=70B3D57ED0020B11 AppID=myloracat-test AppKey=0123456789ABCDEF0123456789ABCDEF DevEUI=0002CC010000007D DevID=myloracat-test-0002cc010000007d

TTN COMMAND: ttnctl devices info --handler-id=ttn-handler-eu myloracat-test-0002cc010000007d
TTNCTL - Device Info:
  INFO Using Application                        AppEUI=70B3D57ED0020B11 AppID=myloracat-test
  INFO Discovering Handler...                   Handler=ttn-handler-eu
  INFO Connecting with Handler...               Handler=eu.thethings.network:1904
  INFO Found device

  Application ID: myloracat-test
       Device ID: myloracat-test
       Last Seen: never

    LoRaWAN Info:

     AppEUI: 70B3D57ED0020B11
     DevEUI: 005AB6DA3EFB7B17
    DevAddr: <nil>
     AppKey: 0123456789ABCDEF0123456789ABCDEF
    AppSKey: <nil>
    NwkSKey: <nil>
     FCntUp: 0
   FCntDown: 0
    Options: FCntCheckEnabled, 32BitFCnt

APPEUI: 70B3D57ED0020B11
DEVEUI: 005AB6DA3EFB7B17
APPKEY: 0123456789ABCDEF0123456789ABCDEF

DoScript: catenainit-otaa.cat
>>> lorawan configure deveui 0002CC010000007D

<<< OK

>>> lorawan configure appeui 70B3D57ED0020B11

<<< OK

>>> lorawan configure appkey 0123456789ABCDEF0123456789ABCDEF

<<< OK

>>> lorawan configure fcntup 0

<<< OK

>>> lorawan configure fcntdown 0

<<< OK

>>> lorawan configure appskey 0

<<< OK

>>> lorawan configure nwkskey 0

<<< OK

>>> lorawan configure join 1

<<< OK

Port /dev/cu.usbmodem621 closed
No errors detected

```

## `mcci-catena-provision-actility.py`

This script communicates with catena to get information for register it in Actility network via Thingpark Enterprise API, then it loads the catena script to device for complete the provisioning process.

### Required

* Python 3.* (Installation steps [here](https://realpython.com/installing-python/))
* Install Python packages [pyserial](https://pyserial.readthedocs.io/en/latest/pyserial.html#installation), [requests](https://requests.readthedocs.io/en/master/) and [ruamel.yaml](https://yaml.readthedocs.io/en/latest/) using following commands in terminal/command prompt:
  1. `pip install pyserial`
  2. `pip install requests`
  3. `pip install ruamel.yaml`
* Actility user account
* Catena Script File (It should be placed in the same repository as the script)

### Notes

1. You need to chose a directory for this script and supporting materials.
If you use `git clone`, you'll specify the target directory; if you download
the zip file from git, then you'll need to choose a place to unpack the
files.

2. Once the files are unpacked, please open the `actility-config.yml` file and 
edit client_id & client_credentials. For e.g. client_id : tpe-eu-api/xxxxx@yyy.com, 
client_credentials: \<your_password\>

### Using `mcci-catena-provision-actility.py`

```
python mcci-catena-provision-actility.py -[options]
```

`-[options]` may be any of the following:

* `-D` - enables debug output.
* `-port` - selects the COM port to be used. For Example: `-port COM11` (windows) or `-port /dev/tty*` (linux) or `-port /dev/cu.*` (Mac)
* `-baud` - sets the desired baud rate. The default is 115200.
* `-info` - outputs information about the Catena to STDOUT.
* `-v` - selects verbose mode.
* `-V` - name=value defines a variable named name, which can subsequently be used in ttnctl application configuration. This option is cumulative. You may use it many times to define different variables. For example, `-V APPEUI=000A000100000047 APPKEY=0123456789ABCDEF0123456789ABCDEF BASENAME=mycatena4470- MODEL=LORA/GenericA.1revB_IN865_Rx2-SF12 APPID=mcci_chennai_mqtt_server`
* `-echo` - causes script lines.
* `-nowrite` - disable writing commands from script file to the Catena.
* `-s` - specifies the mcci-catena-provision script to be used for loading the information into the Catena.
* `-Werror` - says that any warning messages should be promoted to errors, resulting in error messages and non-zero exit status.

### Catena Script File

A number of provisioning scripts are provided for setting up Catenas; the
files are named as `{script}.cat`. If your Catena has already been set up at
the factory, you can use `catena-otaa.cat`.  Here are the scripts by name
and function:

* `catenainit-otaa.cat` - Configure a Catena for OTAA
* `catena-4610-base-otaa.cat` - Configure a Catena 4610 in production
* `catena-4617-otaa.cat` - Configure a Catena 4617 in production
* `catena-4618-otaa.cat` - Configure a Catena 4618 in production
* `catena-4630-otaa.cat` - Configure a Catena 4630 in production

The scripts conventionally get information from variables that are set up
by you or by the script. The variables are:

* `BASENAME` - The base name to be used for devices. This must be a legal
DNS-like name (letters, digits and dashes). The device EUI is appended to
the name. If you want a dash as a separator between the basename and the
DEVEUI, you must end the basename value with a dash.
* `APPEUI` - The Application EUI is a unique 64 bit identifier for the application on the network.
* `DEVEUI` - The device EUI is a unique 64 bit identifier for the end-device on the network.
* `APPKEY` - The App key is a unique 128 bit identifier which used to secure the communication between the device and the network. It is only known by the device and by the application.

### Example (`mcci-catena-provision-actility.py`)

```
python mcci-catena-provision-actility.py -D -port COM25 -V BASENAME=catprov- APPEUI=70B3D53260000246 APPKEY=0123456789ABCDEF0123456789ABCDEF MODEL=LORA/GenericA.1revB_IN865_Rx2-SF12 APPID=mcci_chennai_mqtt_server -s catenainit-otaa.cat

Port COM25 opened
>>> system echo off

<<< system echo off
OK

CheckComms
>>> system version

<<< Board: Catena 4470
Platform-Version: 0.17.0.50
Arduino-LoRaWAN-Version: 0.6.0.20
Arduino-LMIC-Version: 3.0.99.5
MCCIADK-Version: 0.2.1
MCCI-Arduino-BSP-Version: 2.1.0
OK

>>> system configure syseui

<<< 00-02-cc-01-00-00-01-93
OK

Device Created:
{'ref': '1421589', 'name': 'catprov-0193', 'EUI': '0002CC0100000193', 'activationType': 'OTAA', 'deviceProfileId': 'LORA/GenericA.1revB_IN865_Rx2-SF12', 'connectivityPlanId': 'actility-tpe-cs/tpe-cp', 'processingStrategyId': 'ROUTE', 'routeRefs': ['40344'], 'applicationEUI': '70B3D53260000246'}

Device Info:
{'ref': '1421589', 'name': 'catprov-0193', 'EUI': '0002CC0100000193', 'activationType': 'OTAA', 'deviceClass': 'A', 'deviceProfileId': 'LORA/GenericA.1revB_IN865_Rx2-SF12', 'connectivityPlanId': 'actility-tpe-cs/tpe-cp', 'processingStrategyId': 'ROUTE', 'routeRefs': ['40344'], 'applicationEUI': '70B3D53260000246', 'commercialDetails': {'image': '/thingpark/wireless/rest/resources/files/logo/deviceProfile/7453', 'manufacturerName': 'Generic', 'manufacturerLogo': '/thingpark/wireless/rest/resources/files/logo/device/202'}}

DoScript: catenainit-otaa.cat
>>> lorawan configure deveui 0002CC0100000193

<<< OK

>>> lorawan configure appeui 70B3D53260000246

<<< OK

>>> lorawan configure appkey 0123456789ABCDEF0123456789ABCDEF

<<< OK

>>> lorawan configure fcntup 0

<<< OK

>>> lorawan configure fcntdown 0

<<< OK

>>> lorawan configure appskey 0

<<< OK

>>> lorawan configure nwkskey 0

<<< OK

>>> lorawan configure join 1

<<< OK

Port COM25 closed
No errors detected

```

## `mcci-catena-provision-helium.py`

This script communicates with catena to get information for register it in Helium network via Helium console cli, then it loads the catena script to device for complete the provisioning process.

### Required

* Python 3.* (Installation steps [here](https://realpython.com/installing-python/))
* Install Python packages [pyserial](https://pyserial.readthedocs.io/en/latest/pyserial.html#installation) and [pexpect](https://pexpect.readthedocs.io/en/stable/install.html) using following commands in terminal/command prompt:
  1. `pip install pyserial`
  2. `pip install pexpect`
* Helium console CLI. Download it [here](https://github.com/helium/helium-console-cli/releases)
* Catena Script File (It should be placed in the same repository as the script)

### Notes

1. You need to chose a directory for this script and supporting materials.
If you use `git clone`, you'll specify the target directory; if you download
the zip file from git, then you'll need to choose a place to unpack the
files.

2. Once the files are unpacked, you'll also need to get some additional
files, in particular `helium-console-cli`. You can put this on your executable path, but
the easiest thing is to put it in the same directory as the script.

3. The first time you use the CLI, you will need to provide an API key. To create an 
account key, go to your [profile](https://console.helium.com/profile) on 
Helium Console. From the top right corner, click: `Account -> Profile`. From there, 
you may generate a key with a specific name and role. The key will only display once. 
The first time you run the provisioning script, it will prompt you for this key. It 
will save the key in a local file: `.helium-console-config.toml`.

### Using `mcci-catena-provision-helium.py`

```bash
python mcci-catena-provision-helium.py -[options]
```

`-[options]` may be any of the following:

* `-D` - enables debug output.
* `-port` - selects the COM port to be used. For Example: `-port COM11` (windows) or `-port /dev/tty*` (linux) or `-port /dev/cu.*` (Mac)
* `-baud` - sets the desired baud rate. The default is 115200.
* `-info` - outputs information about the Catena to STDOUT.
* `-v` - selects verbose mode.
* `-V` - name=value defines a variable named name, which can subsequently be used in ttnctl application configuration. This option is cumulative. You may use it many times to define different variables. For example, `-V APPEUI=000A000100000047 APPKEY=0123456789ABCDEF0123456789ABCDEF BASENAME=mycatena4470-`
* `-echo` - causes script lines.
* `-nowrite` - disable writing commands from script file to the Catena.
* `-s` - specifies the mcci-catena-provision script to be used for loading the information into the Catena.
* `-Werror` - says that any warning messages should be promoted to errors, resulting in error messages and non-zero exit status.

### Catena Script File

A number of provisioning scripts are provided for setting up Catenas; the
files are named as `{script}.cat`. If your Catena has already been set up at
the factory, you can use `catena-otaa.cat`.  Here are the scripts by name
and function:

* `catenainit-otaa.cat` - Configure a Catena for OTAA
* `catena-4610-base-otaa.cat` - Configure a Catena 4610 in production
* `catena-4617-otaa.cat` - Configure a Catena 4617 in production
* `catena-4618-otaa.cat` - Configure a Catena 4618 in production
* `catena-4630-otaa.cat` - Configure a Catena 4630 in production

The scripts conventionally get information from variables that are set up
by you or by the script. The variables are:

* `BASENAME` - The base name to be used for devices. This must be a legal
DNS-like name (letters, digits and dashes). The device EUI is appended to
the name. If you want a dash as a separator between the basename and the
DEVEUI, you must end the basename value with a dash.
* `APPEUI` - The Application EUI is a unique 64 bit identifier for the application on the network.
* `DEVEUI` - The device EUI is a unique 64 bit identifier for the end-device on the network.
* `APPKEY` - The App key is a unique 128 bit identifier which used to secure the communication between the device and the network. It is only known by the device and by the application.

### Example (`mcci-catena-provision-helium.py`)

```console
python mcci-catena-provision-helium.py -D -port COM25 -V APPEUI=000A000100000047 APPKEY=0123456789ABCDEF0123456789ABCDEF BASENAME=catena4470- -s catenainit-otaa.cat

Port COM25 opened
>>> system echo off

<<< system echo off
OK

CheckComms
>>> system version

<<< Board: Catena 4470
Platform-Version: 0.17.0.50
Arduino-LoRaWAN-Version: 0.6.0.20
Arduino-LMIC-Version: 3.0.99.5
MCCIADK-Version: 0.2.1
MCCI-Arduino-BSP-Version: 2.1.0
OK

>>> system configure syseui

<<< 00-02-cc-01-00-00-01-93
OK
using light sleep

HELIUM COMMAND: helium-console-cli device create 000A000100000047 0123456789ABCDEF0123456789ABCDEF 0002CC0100000193 catena4470-0002cc0100000193
HELIUM - Device Registered:
 Device {
    app_eui: "000A000100000047",
    app_key: "0123456789ABCDEF0123456789ABCDEF",
    dev_eui: "0002CC0100000193",
    id: "1d4b7fcd-3a61-40a3-93d0-7b50642648d9",
    name: "catena4470-0002cc0100000193",
    organization_id: "542a0c22-248c-423a-ad29-30a58e68543d",
    oui: 1,
}

HELIUM COMMAND: helium-console-cli device get 000A000100000047 0123456789ABCDEF0123456789ABCDEF 0002CC0100000193
HELIUM - Device Info:
 Device {
    app_eui: "000A000100000047",
    app_key: "0123456789ABCDEF0123456789ABCDEF",
    dev_eui: "0002CC0100000193",
    id: "1d4b7fcd-3a61-40a3-93d0-7b50642648d9",
    name: "catena4470-0002cc0100000193",
    organization_id: "542a0c22-248c-423a-ad29-30a58e68543d",
    oui: 1,
}

APPEUI: 000A000100000047
DEVEUI: 0002CC0100000193
APPKEY: 0123456789ABCDEF0123456789ABCDEF

Device Created Successfully
DoScript: catenainit-otaa.cat
>>> lorawan configure deveui 0002CC0100000193

<<< OK

>>> lorawan configure appeui 000A000100000047

<<< OK

>>> lorawan configure appkey 0123456789ABCDEF0123456789ABCDEF

<<< OK

>>> lorawan configure fcntup 0

<<< OK

>>> lorawan configure fcntdown 0

<<< OK

>>> lorawan configure appskey 0

<<< OK

>>> lorawan configure nwkskey 0

<<< OK

>>> lorawan configure join 1

<<< OK

Port COM25 closed
No errors detected

```

## Credits

* Written by [Terry Moore](https://linkedin.com/in/terrillmoore)
* Sponsored by [MCCI Corporation](http://www.mcci.com), [The Things Network New York](https://thethings.nyc) and [The Things Network Ithaca](https://ttni.tech).
