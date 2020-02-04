#!/bin/sh

echo "entering kernel_recompile.sh"

if [ "${1}" = '--menuconfig' ];
then
    menuconfig="${1}"
    shift
elif [ "${1}" = '--nconfig' ];
then
    menuconfig="${1}"
    shift
else
    menuconfig=""
fi

if [ "${1}" = '--force' ];
then
    force="${1}"
    shift
else
    force=""
    #echo "force: ${force}"
fi

if [ "${1}" = '--no-check-boot' ];
then
    no_check_boot="${1}"
    shift
else
    no_check_boot=""
fi

if [ -n "${no_check_boot}" ];
then
    echo "skipped checking if /boot was mounted"
else
    test -s /boot/grub/grub.cfg || { echo "/boot/grub/grub.cfg not found. Exiting." ; exit 1 ; }
    ls /boot/vmlinuz || { echo "mount /boot first. Exiting." && exit 1 ; }
fi

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

#    --zfs \
compile_kernel()
{
    emerge genkernel -u
    emerge sys-fs/zfs -u       # handle a downgrade from -9999 before genkernel calls @module-rebuild
    #emerge @module-rebuild      # linux-gpib fails if gcc was upgraded unless this is done first  #nope. was confused
    #emerge sci-libs/linux-gpib -u  # might fail if gcc was upgraded and the kernel hasnt been recompiled yet
    genkernel all \
    $menuconfig \
    --no-clean \
    --symlink \
    --module-rebuild \
    --all-ramdisk-modules \
    --makeopts="-j12"
}

#    --callback="/usr/bin/emerge zfs zfs-kmod sci-libs/linux-gpib-modules @module-rebuild" || exit 1
#    --callback="/usr/bin/emerge zfs zfs-kmod sci-libs/linux-gpib sci-libs/linux-gpib-modules @module-rebuild" || exit 1


if [ -e "/usr/src/linux/init/.init_task.o.cmd" ];
then
    echo "found previously compiled kernel tree, checking is the current gcc version was used"
    gcc_ver=`gcc-config -l | grep '*' | cut -d '-' -f 5 | cut -d ' ' -f 1`
    echo "checking for gcc version: ${gcc_ver}"
    grep gcc/x86_64-pc-linux-gnu/"${gcc_ver}" /usr/src/linux/init/.init_task.o.cmd > /dev/null || \
        { echo "old gcc version detected, make clean required. Sleeping 5." && cd /usr/src/linux && sleep 5 && make clean ; } && echo "gcc ${gcc_ver} was used to compile kernel previously, not running \"make clean\""
fi


#https://www.mail-archive.com/lede-dev@lists.infradead.org/msg07290.html
export | grep "KCONFIG_OVERWRITECONFIG=\"1\"" || \
    { echo "KCONFIG_OVERWRITECONFIG=1 needs to be set" ; \
      echo "you may want to add it to /etc/env.d/99kconfig-symlink Exiting."; exit 1 ; }

if [ -f /usr/src/linux/.config ]; then
    if [ ! -h /usr/src/linux/.config ]; then
        mv /usr/src/linux/.config /home/cfg/sysskel/usr/src/linux_configs/.config.`date +%s`
    fi
fi
test -e /usr/src/linux/.config || ln -s /home/cfg/sysskel/usr/src/linux_configs/.config /usr/src/linux/.config

cd /usr/src/linux || exit 1


if [ -n "${menuconfig}" ];
then
    compile_kernel
elif [ ! -s "/boot/initramfs" ] && [ ! -e "/usr/src/linux/include/linux/kconfig.h" ]; # -s follows symlinks
then
    compile_kernel
else
    echo "/boot/initramfs exists, checking if /usr/src/linux is configured"
    if [ ! -e "/usr/src/linux/init/.init_task.o.cmd" ];
    then
        echo "compiling kernel"
        compile_kernel
    else
        echo "found configured /usr/src/linux, skipping recompile."
    fi
fi


if [ -n "${force}" ];
then
    compile_kernel
fi

rc-update add zfs-import boot
rc-update add zfs-share default
rc-update add zfs-zed default


grub-mkconfig -o /boot/grub/grub.cfg

mkdir /boot_backup
cd /boot_backup
test -d /boot_backup/.git || git init
now=`date +%s`
mkdir "${now}"
cp -ar /boot "${now}"/
git add "${now}" --force
git commit -m "${now}"



echo "kernel compile and install completed OK"
