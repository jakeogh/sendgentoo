#!/usr/bin/env bash

argcount=1
usage="boot_device"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

device="${1}"
test -b "${device}" || { echo "${device} not found or is not a block device. Exiting." > /dev/stderr ; exit 1 ; }
mount | grep "${device}" && { echo "${device} is mounted. Exiting." ; exit 1 ; }

#grep "${device}" gpart_make_hybrid_mbr.exp || { echo "gpart_makr_hybrid_mbr.exp does not contain ${device}, exiting." ; exit 1 ; }

./gpart_make_hybrid_mbr.exp "${device}"


