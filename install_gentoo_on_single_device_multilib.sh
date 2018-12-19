#!/bin/sh

argcount=2
usage="device hostname"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

device="${1}"
shift
mount | grep "${device}" && { echo "ERROR: device: ${device} appears to be mounted. Exiting." ; exit 1 ; }

hostname="${1}"
shift
test -z "${hostname}" && { echo "ERROR: hostname: ${hostname} is length zero" ; exit 1 ; } #just double checking

./umount_mnt_gentoo.sh || ./umount_mnt_gentoo.sh
./umount_mnt_gentoo.sh || ./umount_mnt_gentoo.sh
./umount_mnt_gentoo.sh || ./umount_mnt_gentoo.sh

/home/cfg/setup/gentoo_installer/pre_chroot.py "${device}" \
 --boot-device "${device}" \
 --boot-device-partition-table gpt \
 --root-device-partition-table gpt \
 --boot-filesystem ext4 \
 --root-filesystem ext4 \
 --c-std-lib glibc \
 --hostname "${hostname}" \
 --march nocona \
 --raid disk \
 --multilib \
 --raid-group-size 1

# --force \

