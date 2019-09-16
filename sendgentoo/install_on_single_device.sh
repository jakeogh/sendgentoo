#!/bin/sh

#echo "fix /usr/portage/packages first"
#exit 1

argcount=2
usage="device ip"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

[ -z "${TMUX}" ] && { echo "not in tmux" ; exit 1 ; }

device="${1}"
shift
ip="${1}"
shift

mount | grep "${device}" && { echo "ERROR: device: ${device} appears to be mounted. Exiting." ; exit 1 ; }
test -b "${device}" || { echo "ERROR: device: ${device} is not block special. Exiting." ; exit 1 ; }


./umount_mnt_gentoo.sh || ./umount_mnt_gentoo.sh
./umount_mnt_gentoo.sh || ./umount_mnt_gentoo.sh
./umount_mnt_gentoo.sh || ./umount_mnt_gentoo.sh

echo -n "Enter new password: "
read newpasswd

/home/cfg/setup/gentoo_installer/pre_chroot.py "${device}" \
 --boot-device "${device}" \
 --boot-device-partition-table gpt \
 --root-device-partition-table gpt \
 --boot-filesystem ext4 \
 --root-filesystem ext4 \
 --c-std-lib glibc \
 --hostname glibc128gbssdext4 \
 --march native \
 --raid disk \
 --raid-group-size 1 \
 --newpasswd "${newpasswd}" \
 --ip "${ip}"

# --force \

