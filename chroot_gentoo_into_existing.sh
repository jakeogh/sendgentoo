#!/bin/bash

argcount=2
usage="boot_device root_device"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

boot_device="${1}"
root_device="${1}"

mount | grep '/mnt/gentoo' || mount "${root_device}" /mnt/gentoo # bug, deal with seperate boot_device

echo "checking /proc /sys and /dev mounts in prep to chroot"
mount | grep '/mnt/gentoo/proc' || { mount -t proc none /mnt/gentoo/proc || exit 1 ; }
mount | grep '/mnt/gentoo/sys' || { mount --rbind /sys /mnt/gentoo/sys || exit 1 ; }
mount | grep '/mnt/gentoo/dev' || { mount --rbind /dev /mnt/gentoo/dev || exit 1 ; }

echo "bind mounting /usr/portage"
test -d /mnt/gentoo/usr/portage || { mkdir -p /mnt/gentoo/usr/portage || exit 1 ; }
mount | grep '/mnt/gentoo/usr/portage' || { mount --rbind /usr/portage /mnt/gentoo/usr/portage || exit 1 ; }


echo "Entering chroot"
#chroot /mnt/gentoo /bin/bash -c "su - -c '/home/cfg/setup/gentoo_installer/gentoo_setup_post_chroot.sh ${stdlib} ${boot_device} ${hostname} ${cflags} ${root_filesystem}'"
#env -i HOME=/root TERM=$TERM chroot /mnt/gentoo /bin/bash -l -c "su - -c '/home/cfg/setup/gentoo_installer/gentoo_setup_post_chroot.sh ${stdlib} ${boot_device} ${hostname} ${cflags} ${root_filesystem}'" || { echo "gentoo_setup_post_chroot.sh exited $?" ; exit 1 ; }
env -i HOME=/root TERM=$TERM chroot /mnt/gentoo /bin/bash -l || { echo "gentoo_setup_post_chroot.sh exited $?" ; exit 1 ; }
#chroot /mnt/gentoo /bin/bash -c "su - -c '/bin/bash'"

#eclean-pkg -d #remove outdated binary packages before cp

#umount /mnt/gentoo/usr/portage && cp -avr /usr/portage/packages /mnt/gentoo/usr/portage/ && mkdir /mnt/gentoo/usr/portage/distfiles && cp /usr/portage/distfiles/*stage3* /mnt/gentoo/usr/portage/distfiles/

#/home/cfg/setup/gentoo_installer/umount_mnt_gentoo.sh
#/home/cfg/setup/gentoo_installer/gpart_make_hybrid_mbr.sh

#echo "gentoo install complete! might need to fix grub.cfg"
