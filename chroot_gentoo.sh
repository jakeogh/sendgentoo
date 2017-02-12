#!/bin/bash

argcount=5
usage="stdlib boot_device hostname cflags root_filesystem"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

stdlib="${1}"
boot_device="${2}"
hostname="${3}"
cflags="${4}"
root_filesystem="${5}"

echo "checking /proc /sys and /dev mounts in prep to chroot"
mount | grep '/mnt/gentoo/proc' || { mount -t proc none /mnt/gentoo/proc || exit 1 ; }
mount | grep '/mnt/gentoo/sys' || { mount --rbind /sys /mnt/gentoo/sys || exit 1 ; }
mount | grep '/mnt/gentoo/dev' || { mount --rbind /dev /mnt/gentoo/dev || exit 1 ; }

echo "bind mounting /usr/portage"
test -d /mnt/gentoo/usr/portage || { mkdir -p /mnt/gentoo/usr/portage || exit 1 ; }
mount | grep '/mnt/gentoo/usr/portage' || { mount --rbind /usr/portage /mnt/gentoo/usr/portage || exit 1 ; }

echo "making /mnt/gentoo/home/cfg"
test -d /mnt/gentoo/home/cfg || { mkdir -p /mnt/gentoo/home/cfg || exit 1 ; }
#mount | grep '/mnt/gentoo/home/cfg' || { mount --rbind /home/cfg /mnt/gentoo/home/cfg || exit 1 ; }

test -d /mnt/gentoo/usr/local/portage || { mkdir -p /mnt/gentoo/usr/local/portage || exit 1 ; }

echo "cp -ar /home/cfg /mnt/gentoo/home/"
#time cp -ar /home/cfg /mnt/gentoo/home/ || exit 1
time (cd /home && tar zcf - cfg ) | pv -trabT -B 600M | (cd /mnt/gentoo/home && tar zxpSf - )

#test -h /mnt/gentoo/boot/vmlinuz || { cp -af /boot/* /mnt/gentoo/boot/ || exit 1 ; }

if [[ "${root_filesystem}" == 'zfs' ]];
then
    mkdir -p /mnt/gentoo/etc/zfs
    cp /etc/zfs/zpool.cache /mnt/gentoo/etc/zfs/zpool.cache
fi

echo "Entering chroot"
#chroot /mnt/gentoo /bin/bash -c "su - -c '/home/cfg/setup/gentoo_installer/gentoo_setup_post_chroot.sh ${stdlib} ${boot_device} ${hostname} ${cflags} ${root_filesystem}'"
env -i HOME=/root TERM=$TERM chroot /mnt/gentoo /bin/bash -l -c "su - -c '/home/cfg/setup/gentoo_installer/gentoo_setup_post_chroot.sh ${stdlib} ${boot_device} ${hostname} ${cflags} ${root_filesystem}'" || { echo "gentoo_setup_post_chroot.sh exited $?" ; exit 1 ; }
#chroot /mnt/gentoo /bin/bash -c "su - -c '/bin/bash'"

eclean-pkg -d #remove outdated binary packages before cp

umount /mnt/gentoo/usr/portage && cp -avr /usr/portage/packages /mnt/gentoo/usr/portage/ && mkdir /mnt/gentoo/usr/portage/distfiles && cp /usr/portage/distfiles/*stage3* /mnt/gentoo/usr/portage/distfiles/

/home/cfg/setup/gentoo_installer/umount_mnt_gentoo.sh
/home/cfg/setup/gentoo_installer/gpart_make_hybrid_mbr.sh

echo "gentoo install complete! might need to fix grub.cfg"
