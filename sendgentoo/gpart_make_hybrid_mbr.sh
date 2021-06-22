#!/usr/bin/env bash

argcount=1
usage="boot_device"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

device="${1}"
test -b "${device}" || { echo "$0: ${device} not found or is not a block device. Exiting." > /dev/stderr ; exit 1 ; }
#mount | grep "${device}" && { echo "$0: ${device} is mounted. Exiting." ; exit 1 ; }

echo "$0: making hybrid MBR"
/home/cfg/_myapps/sendgentoo/sendgentoo/gpart_make_hybrid_mbr.exp "${device}" || exit 1
echo "$0: making hybrid MBR exited 0, should be good to go."
