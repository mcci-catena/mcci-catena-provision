# mcci-catena-provision

Set up an MCCI Catena via serial console (USB or regular)

This repository contains a program `mcci-catena-provision.py` which loads one or more network provisioning scripts into an MCCI Catena device built using the [Catena-Arduino-Platform](https://github.com/mcci-catena/Catena-Arduino-Platform). It was primarily developed for configuring Catena boards for use with the [The Things Network](https://thethingsnetwork.org). However, the tool can be used for other purposes as desired.

It provides a streamlined registration flow when working with The Things Network. It registers the device with the network, then uses `mcci-catena-provision` to load the network-generated application credentials into the Catena.

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
  - [`mcci-catena-provision.py`](#mcci-catena-provisionpy)
    - [Required](#required)
    - [Notes](#notes)
    - [Using `mcci-catena-provision.py`](#using-mcci-catena-provisionpy)
    - [Catena Script File](#catena-script-file)
    - [Example](#example)
  - [Credits](#credits)

<!-- /TOC -->
<!-- markdownlint-restore -->
<!-- Due to a bug in Markdown TOC, the table is formatted incorrectly if tab indentation is set other than 4. Due to another bug, this comment must be *after* the TOC entry. -->

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

### Example

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
  INFO Registered device                        AppEUI=70B3D57ED0020B11 AppID=myloracat-test AppKey=3F7C97348A9F938BE3805CAE51A30B22 DevEUI=0002CC010000007D DevID=myloracat-test-0002cc010000007d

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
     AppKey: BF0A14350226F2760017F43C9B72D8FF
    AppSKey: <nil>
    NwkSKey: <nil>
     FCntUp: 0
   FCntDown: 0
    Options: FCntCheckEnabled, 32BitFCnt

APPEUI: 70B3D57ED0020B11
DEVEUI: 005AB6DA3EFB7B17
APPKEY: BF0A14350226F2760017F43C9B72D8FF

DoScript: catenainit-otaa.cat
>>> lorawan configure deveui 0002CC010000007D

<<< OK

>>> lorawan configure appeui 70B3D57ED0020B11

<<< OK

>>> lorawan configure appkey BF0A14350226F2760017F43C9B72D8FF

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

## Credits

* Written by [Terry Moore](https://linkedin.com/in/terrillmoore)
* Sponsored by [MCCI Corporation](http://www.mcci.com), [The Things Network New York](https://thethings.nyc) and [The Things Network Ithaca](https://ttni.tech).
