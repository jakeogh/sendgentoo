#!/bin/sh

#mount | grep '/boot' || { echo "mount /boot first. Exiting." && exit 1 ; }
ls /boot/vmlinuz || { echo "mount /boot first. Exiting." && exit 1 ; }

test -e /usr/src/linux/.config || ln -s /home/cfg/sysskel/usr/src/linux_configs/.config /usr/src/linux/.config

cd /usr/src/linux && make menuconfig && ~/cfg/pause && make -j12 && make install && make modules_install || exit 1
echo "kernel compile and install completed OK"

qpkg zfs && USE="${USE} -kernel-builtin" emerge spl zfs zfs-kmod || { echo "xfs is not installed, skipping \"emerge zfs\"" ; }
qpkg zfs && genkernel initramfs --no-clean --no-mountboot --zfs --symlink
