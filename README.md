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

## Credits

* Written by [Terry Moore](https://linkedin.com/in/terrillmoore)
* Sponsored by [MCCI Corporation](http://www.mcci.com), [The Things Network New York](https://thethings.nyc) and [The Things Network Ithaca](https://ttni.tech).
