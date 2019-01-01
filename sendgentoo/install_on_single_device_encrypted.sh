#!/bin/sh

argcount=1
usage="device"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

device="${1}"
shift
mount | grep "${device}" && { echo "ERROR: device: ${device} appears to be mounted. Exiting." ; exit 1 ; }

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
 --hostname glibc128gbssdext4 \
 --march nocona \
 --raid disk \
 --raid-group-size 1 \
 --encrypt


