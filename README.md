# mcci-load-mote-profile
Load a profile into a Microchip mote

This program (for Windows only at the moment) loads one or more setting
scripts into a Microchip RN2903 LoRa Mote. It was primarily developed for
configuring RN2903's for immediate use with the US915 variant of
[The Things Network](https://thethingsnetwork.org). However, the tool can be used for other purposes as desired.

----
## Overview

mcci-load-mote-profile reads one or more scripts containing RN2903 commands, sending each line sequentially to an RN2903 directly connected to the PC via USB, and checking the results. Simple variable substitution allows you to input provisioning information from the command line, if needed.

Several scripts (`.mot` files, where `mot` is short for "mote") are provided with the package, to perform common tasks. These include:

* `moteinit-otaa.mot` -- initialize a mote for LoRa over-the-air authentication ("OTAA"), using information provided from the command line. See "Using `moteinit-otaa.mot`", below.
* `moteinit-subband2.mot` -- initialize a mote for sub-band 2 of the US915 spectrum plan. This should be used for The Things Network.
* `moteinit-subband7.mot` -- initialize a mote for subband 7 of the US915 spectrum plan. This was used prior to May 2016.
* `mote-save.mot` -- cause the Mote to write all settings to non-volatile memory. This should be used as the last script in a collection. The mote will otherwise lose the settings when you unplug the USB cable.

----
## Usage
    ./bright mcci-load-mote-profile.bri -[options] [scripts ...]

The components of this command may be understood as follows.

`bright mcci-load-mote-profile.bri` invokes Terry Moore's [Bright interpreter](http://www.lua.org/wshop08.html#moore), which is included (in compiled form) in this package, to run `mcci-load-mote-profile.bri`. (Sources for Bright are available from Terry, contact author for information; posting to GitHub is pending.)

`-[options]` may be any of the following. Options are processed left to right. Unless we say otherwise, the rightmost option overrides any previous option setting. Boolean options may be negated using the "no" prefix; so for example write "`-noD`" to explicitly negate any previous `-D` option.

* `-baudrate #` sets the desired baud rate. The default is 57600, which is what the Mote documentation suggests.
* `-D` enables debug output to STDERR.
* `-echo` causes script lines 
* `-help` outputs a brief reference, and exits.
* `-info` outputs information about the Mote to STDOUT. This is intended to be used without any script files, in order to get information about the Mote being programmed.
* `-port` _portname_ selects the COM port to be used. It should usually be of the form `com1`, `com2`, etc. You can use Windows Device Manager > Ports (Com & LPT) to get a list of available ports.
* `-V` _name_=_value_ defines a variable named _name_, which can subsequently be used in script files (see "Script File Syntax", below). __This option is cumulative__. You may use it many times to define different variables.
* `-v` selects verbose mode. Additional messages are logged to STDERR.
* `-write` enables writing commands to the Mote. This is the default. `-nowrite` can be used on the command line to cause `mcci-load-mote-profiles.bri` to go through all the motions (macro expansion, etc) but not download any data to the mote. This is intended for use when debugging scripts.
* `-Werror` says that any warning messages should be promoted to errors, resulting in error messages and non-zero exit status.

----
## Mote Script File Syntax

Mote script files are processed line by line. Blank lines, and lines beginning with whitespace followed by `#` are treated as comments and ignored.

Otherwise the line is macro-expanded and then sent to the Mote.

Macros are indicated using the syntax `${NAME}`, where `NAME` is either a special variable defined by `mcci-load-mote-profile` or else a variable defined using the `-V` option on the command line. An undefined variable will cause `mcci-load-mode-profile` to report an error.

The special variable `SYSEUI` is always set to the system EUI read from the Mote. 

### Scripting Reference
The scripting commands are defined by the Microtech [LoRa Mote User's Guide](http://ww1.microchip.com/downloads/en/DeviceDoc/LoRa%20Mote%20Users%20Guide.pdf). Revision B was used for preparing the scripts in this package.


----
## Using `moteinit-otaa.mot`

The OTAA script `moteinit-otaa.mot` expects that you will invoke `mcci-load-mote-profile.bri` with the following `-V` definitions:

* `-V APPEUI=0123456789abcdef` -- this is 16-digit application EUI in hex, as displayed by `ttnctl` when you register your device. (Don't worry about byte reversal issues.)
* `-V APPKEY=0123456789abcdef0123456789abcdef` -- this is the 32-digit application key assigned to your device by `ttnctl` when you register your device.

A simple workflow is:

1. Connect your Mote to your PC with a USB cable.
2. Get your device's EUI using `mcci-load-mote-profile.bri` and the `-info` option.
3. Use that EUI to register your device using `ttnctl`.
4. Run `mcci-load-mote-profile.bri` again with the `moteinit-otaa.mot` script, specifying the AppEUI and the AppKey displayed by `ttnctl`.

Here's an example.

    $ ./bright mcci-load-mote-profile.bri -port com11 -info
    MoteType: RN2903
    Firmware: 0.9.5
    Date: Sep 02 2015 17:19:55
    SysEUI: 0004A30B001A2B50

    $ ttnctl devices register 0004A30B001A2B50
      INFO Generating random AppKey...
      INFO Registered device                        AppKey=0123456789ABCDEF0123456789ABCDEF DevEUI=0004A30B001A2B50
    
    $ ttnctl devices info 0004A30B001A2B50
    Dynamic device:
    
      AppEUI:  70B3D57ED0000852
               {0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x00, 0x08, 0x52}
    
      DevEUI:  0004A30B001A2B50
               {0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x83, 0xFA}

      AppKey:  0123456789ABCDEF0123456789ABCDEF
           {0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF, 0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF}

    $ ./bright mcci-load-mote-profile.bri -port com11 -echo -V APPEUI=70B3D57ED0000852 -V APPKEY=0123456789ABCDEF0123456789ABCDEF moteinit-otaa.mot  mote-save.mot
    mac set deveui 0004A30B001A2B50
    mac set appeui 70B3D57ED0000852
    mac set appkey 0123456789ABCDEF0123456789ABCDEF
    mac save
    
    $

There's a short pause while the mote is processing the `mac save` command.  

----
# Credits
* Written by [Terry Moore](https://linkedin.com/in/terrillmoore), sponsored by [MCCI Corporation](http://www.mcci.com), [The Things Network New York](https://thethings.nyc) and [The Things Network Ithaca](https://ttni.tech).
