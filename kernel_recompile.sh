#!/bin/sh

am_i_root()
{
    # Sanity Check: Test if the script runs as root
    if [ "$(whoami)" != root ]
    then
        echo -e "\nPlease run this script as root! Exiting.\n" >&2
        exit 1
    fi
}

am_i_root

test -s /boot/grub/grub.cfg || { echo "/boot/grub/grub.cfg not found. Exiting." ; exit 1 ; }

ls /boot/vmlinuz || { echo "mount /boot first. Exiting." && exit 1 ; }

#https://www.mail-archive.com/lede-dev@lists.infradead.org/msg07290.html
export | grep "KCONFIG_OVERWRITECONFIG=\"1\"" || \
    { echo "KCONFIG_OVERWRITECONFIG=1 needs to be set" ; \
      echo "you may want to add it to /etc/env.d/99kconfig-symlink. Exiting."; exit 1 ; }

test -e /usr/src/linux/.config || ln -s /home/cfg/sysskel/usr/src/linux_configs/.config /usr/src/linux/.config

cd /usr/src/linux || exit 1

if [ "${1}" == '--menuconfig' ];
then
    qpkg zfs && \
        genkernel all \
        --menuconfig \
        --no-clean \
        --zfs \
        --symlink \
        --makeopts="-j12" \
        --callback="/usr/bin/emerge zfs zfs-kmod @module-rebuild" || exit 1

    qpkg zfs || \
        genkernel all \
        --menuconfig \
        --no-clean \
        --symlink \
        --makeopts="-j12" || exit 1

    #make menuconfig && ~/cfg/pause && make -j12 && make install && make modules_install || exit 1
else
    qpkg zfs && \
        genkernel all \
        --no-clean \
        --zfs \
        --symlink \
        --makeopts="-j12" \
        --callback="/usr/bin/emerge zfs zfs-kmod @module-rebuild" || exit 1

    qpkg zfs || \
        genkernel all \
        --no-clean \
        --symlink \
        --makeopts="-j12" || exit 1

    #make oldconfig && ~/cfg/pause && make -j12 && make install && make modules_install || exit 1
fi

grub-mkconfig -o /boot/grub/grub.cfg
echo "kernel compile and install completed OK"

#qpkg zfs && USE="${USE} -kernel-builtin" emerge zfs zfs-kmod || \
#    { echo "zfs is not installed, skipping \"emerge zfs\"" ; }
#qpkg zfs && genkernel initramfs --no-clean --no-mountboot --zfs --symlink
#grub-mkconfig -o /boot/grub/grub.cfg

