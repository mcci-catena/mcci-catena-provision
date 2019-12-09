#!/bin/bash

##############################################################################
#
# Module:  provision-from-ttnctl.sh
#
# Function:
# 	Provision a Catena from the ttnctl api.
#
# Copyright notice and License:
# 	See accompanying LICENSE file at 
#	https://github.com/mcci-catena/Catena-Arduino-Platform
#
# Author:
#	Terry Moore, MCCI Corporation	July 2019
#
##############################################################################

readonly PNAME="$(basename "$0")"
readonly PDIR="$(dirname "$0")"
typeset -i OPTDEBUG=0
typeset -i OPTVERBOSE=0

readonly MCCIBRIGHT_LIB="${PDIR}"
export MCCIBRIGHT_LIB

##############################################################################
# verbose output
##############################################################################

function _verbose {
	if [ "$OPTVERBOSE" -ne 0 ]; then
		echo "$PNAME:" "$@" 1>&2
	fi
}

function _debug {
	if [ "$OPTDEBUG" -ne 0 ]; then
		echo "$@" 1>&2
	fi
}

#### _error: define a function that will echo an error message to STDERR.
#### using "$@" ensures proper handling of quoting.
function _error {
	echo "$@" 1>&2
}

#### _fatal: print an error message and then exit the script.
function _fatal {
	_error "$@" ; exit 1
}

function _report {
	echo "$1:"
	echo "$2" | tr ' ' '\n' | column
}


##############################################################################
# Display help
##############################################################################

function _help {
	less << .
Name:	$PNAME

Function:
	Provision a Catena from the ttnctl database

Synopsis:
	ttnctl application select {appID}
	$PNAME [switches] {deviceEUI}

Switches:
	-a {appname}	appname to choose. "-a -" uses the current default.
	-b {basename}	base name of the device, default "device-"
	-p {comport}	specifies the COM port. default is com1.
	-h {handler}	specifies the TTN application handler. Default
			is ttn-handler-us-west.
	-s {catenainit-script} the script to do the setup.
	-v		verbose logging
	-D		debug logging

Environment variables:
	TTNCTL	if set, gives the full pathname of the 'ttnctl' executable
		image. If not set, ttnctl must be found in the current
		PATH.

Description:
	We get basic device info from the com port to confirm that it's connected.

	The device name is then created from the prefix (-b) and the deviceEUI.
	The device is registered with TTNCTL using the current default app.
	We then 


Exit status:
	The exit status will only be zero if both ttnctl and post-processing
	succeed.
.
}

##############################################################################
# Scan the options
##############################################################################

LIBRARY_ROOT="${LIBRARY_ROOT_DEFAULT}"
USAGE="${PNAME} -[a* b* D h* p* s* v] deveui; ${PNAME} -H for help"

#OPTDEBUG and OPTVERBOSE are above
OPTAPPID="-"
OPTBASENAME="device-"
OPTHANDLERID=ttn-handler-us-west
OPTPORT=com1
OPTSCRIPT=catenainit-otaa.cat

NEXTBOOL=1
while getopts a:b:DHh:np:s:v c
do
	# postcondition: NEXTBOOL=0 iff previous option was -n
	# in all other cases, NEXTBOOL=1
	if [ $NEXTBOOL -eq -1 ]; then
		NEXTBOOL=0
	else
		NEXTBOOL=1
	fi

	case "$c" in
	a)	OPTAPPID="$OPTARG";;
	b)	OPTBASENAME="$OPTARG";;
	D)	OPTDEBUG=$NEXTBOOL;;
	n)	NEXTBOOL=-1;;
	p)	OPTPORT="$OPTARG";;
	s)	OPTSCRIPT="$OPTARG";;
	v)	OPTVERBOSE=$NEXTBOOL;;
	H)	_help
		exit 0;;
	h)	OPTHANDLERID="$OPTARG";;
	\?)	echo "$USAGE" 1>&2
		exit 1;;
	esac
done

#### get rid of scanned options ####
shift `expr $OPTIND - 1`

#### make sure we have an deveui
if [[ $# -lt 1 ]]; then
	_fatal "Must supply deveui"
fi

#### verify that it looks like a deveui
if "${PDIR}/bright" -c "D='X$1' ; if (gsub(D, '^X'.. strrep('%x', 16) .. '$', '') != '') exit(1);" ; then
	true
else
	_fatal "not a valid deveui: $1"
fi

# look for ttnctl
if [ X"$TTNCTL" = X ]; then
	if command -v ttnctl > /dev/null ; then 
		TTNCTL=ttnctl
	else
		_fatal "ttnctl not found; add to path, or set TTNCTL to full name of executable"
	fi
fi

# get info from the device
_debug "Get info"
${PDIR}/bright ${PDIR}/mcci-catena-provision.bri -info -permissive -port "${OPTPORT}" || _fatal "can't get info from device on com port $OPTPORT"

# select app
if [[ "$OPTAPPID" != "-" ]]; then
	_verbose "Selecting app -- be patient..."
	$TTNCTL application select "$OPTAPPID" || _fatal "error selecting app"
else
	_verbose "Using default TTN app"
fi

# register the device
_debug "register device"
# create the devid
DEVID="$(printf "%s%s" $OPTBASENAME $1 | tr A-Z a-z)"
_debug "effective DEVID: $DEVID"

"$TTNCTL" devices register "$DEVID" "$1" ${OPTHANDLERID:+--handler-id=${OPTHANDLERID}} || _fatal error registering $1 as $DEVID

# read output into a variable; we'll echo it if ttnctl succeeds
# and consume it otherwise.
_debug "Get device info"
if OUTPUT="$("$TTNCTL" devices info "${OPTHANDLERID:+--handler-id=${OPTHANDLERID}}" "$DEVID"  )" ; then
	SWITCHES="$(echo "$OUTPUT" | awk '
function friendlyHex(s,  r, i)
   { # r, i are local variables
   r = "";
   for (i = 1; i < length(s); i += 2)
      {
      if (r != "")
         r = r "-" substr(s, i, 2);
      else
         r = substr(s, i, 2);
      }
  return r;
  }
 $1 == "AppEUI:" { AppEUI = $2; }
 $1 == "DevEUI:" { DevEUI = $2; DevEUIfriendly = $2; }
 $1 == "AppKey:" { AppKey = $2; }
 END {
     # output settings for substiution in mcci-catena-provision
     printf("-V APPKEY=%s ", AppKey);
     printf("-V DEVEUI=%s ", DevEUI);
     printf("-V APPEUI=%s", AppEUI);
     }
 ')" || _fatal "output parsing failed: " "$OUTPUT"
else
	_fatal "ttnctl failed: " "$OUTPUT"
fi

#### now for testing, just display the switch values.
_debug "Parse result: " $SWITCHES
_verbose provisioning Catena
${PDIR}/bright ${PDIR}/mcci-catena-provision.bri -port ${OPTPORT:-com1} -permissive -echo -v -V DEVEUI=$1 $SWITCHES "${OPTSCRIPT}" || _fatal "Provisioning failed"
