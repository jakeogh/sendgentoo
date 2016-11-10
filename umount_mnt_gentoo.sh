#!/bin/bash

echo "entering check_and_close_mounts()"
echo "checking if the ${root_device} is not block special"
test ! -b "${root_device}" && { echo "root_device: ${root_device} is not block special, normally this would exit here, not sure why though" ; }
umount "${root_device}1"
umount "${root_device}2"

umount -v /mnt/gentoo/proc
umount -l -v /mnt/gentoo/sys
umount -l -v /mnt/gentoo/dev
umount /mnt/gentoo

echo "umounting ${boot_partition}" >> /dev/stderr
umount -v "${boot_partition}" || echo "Unmount failed, this is normal if ${boot_partition} was not already mounted."
umount -v "${boot_partition}" || echo "Unmount failed, this is normal if ${boot_partition} was not already mounted."
mount | grep "${boot_partition}" && { echo "${boot_partition} is still mounted, exiting." ; exit 1 ; }
mount | grep "${root_device}" && { echo "check_and_close_mounts() root_device ${root_device} is mounted. This is unexpected. Exiting" ; exit 1 ; }

mount | grep "${mapper_device}1" && umount "${mapper_device}1"
kpartx -d "${mapper_device}1" || echo "Unable to remove the mapper_device ${mapper_device}1, this is normal if it was not already added to the partition list."
kpartx -d "${mapper_device}" || echo "Unable to remove the mapper_device ${mapper_device}1, this is normal if it was not already added to the partition list."
umount /mnt/gentoo
cryptsetup close "${mapper_device}" || echo "Unable to close ${mapper_device} with cryptsetup, this is normal if it was not already open."

zfs umount rpool/ROOT/gentoo
zfs umount rpool/HOME
zfs umount rpool/HOME/root
zfs umount rpool/GENTOO/portage
zfs umount rpool/GENTOO/distfiles
zfs umount rpool/GENTOO/build-dir
zfs umount rpool/GENTOO/packages
zfs umount rpool/GENTOO/ccache

zfs umount rpool/ROOT/gentoo
zfs umount rpool/GENTOO/portage
zfs umount rpool/ROOT/gentoo

