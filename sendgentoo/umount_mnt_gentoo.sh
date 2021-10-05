#!/bin/bash

umount /mnt/gentoo/var/db/repos/gentoo
umount /mnt/gentoo/dev/shm
umount /mnt/gentoo/dev/pts
umount /mnt/gentoo/dev
umount /mnt/gentoo/sys/fs/cgroup/unified
umount /mnt/gentoo/sys/fs/cgroup/net_prio
umount /mnt/gentoo/sys/fs/cgroup/net_cls
umount /mnt/gentoo/sys/fs/cgroup/memory
umount /mnt/gentoo/sys/fs/cgroup/cpu
umount /mnt/gentoo/sys/fs/cgroup/openrc
umount /mnt/gentoo/sys/fs/cgroup
umount /mnt/gentoo/sys/fs/fuse/connections
umount /mnt/gentoo/sys/firmware/efi/efivars
umount /mnt/gentoo/sys/kernel/config
umount /mnt/gentoo/sys/kernel/debug
umount /mnt/gentoo/sys
umount /mnt/gentoo/proc
umount /mnt/gentoo/boot/efi
umount /mnt/gentoo/usr/portage
umount /mnt/gentoo/sys
umount /mnt/gentoo

mount | grep gentoo | cut -d ' ' -f 3 | xargs -I '{}' umount '{}'

exit 0


#zfs umount rpool/ROOT/gentoo
#zfs umount rpool/HOME
#zfs umount rpool/HOME/root
#zfs umount rpool/GENTOO/portage
#zfs umount rpool/GENTOO/distfiles
#zfs umount rpool/GENTOO/build-dir
#zfs umount rpool/GENTOO/packages
#zfs umount rpool/GENTOO/ccache
#
#zfs umount rpool/ROOT/gentoo
#zfs umount rpool/GENTOO/portage
#zfs umount rpool/ROOT/gentoo
#
