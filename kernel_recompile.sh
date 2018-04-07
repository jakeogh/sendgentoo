#!/bin/sh

test -s /boot/grub/grub.cfg || { echo "/boot/grub/grub.cfg not found. Exiting." ; exit 1 ; }

ls /boot/vmlinuz || { echo "mount /boot first. Exiting." && exit 1 ; }

#https://www.mail-archive.com/lede-dev@lists.infradead.org/msg07290.html
export | grep "KCONFIG_OVERWRITECONFIG=\"1\"" || { echo "KCONFIG_OVERWRITECONFIG=1 needs to be set, you prob want to add it to /etc/env.d/99kconfig-symlink" ; echo "exiting." ; exit 1 ; }

test -e /usr/src/linux/.config || ln -s /home/cfg/sysskel/usr/src/linux_configs/.config /usr/src/linux/.config

cd /usr/src/linux || exit 1

if [ "${1}" == 'menuconfig' ];
then
    make menuconfig && ~/cfg/pause && make -j12 && make install && make modules_install || exit 1
else
    make oldconfig && ~/cfg/pause && make -j12 && make install && make modules_install || exit 1
fi
echo "kernel compile and install completed OK"

qpkg zfs && USE="${USE} -kernel-builtin" emerge spl zfs zfs-kmod || { echo "zfs is not installed, skipping \"emerge zfs\"" ; }
qpkg zfs && genkernel initramfs --no-clean --no-mountboot --zfs --symlink
grub-mkconfig -o /boot/grub/grub.cfg

