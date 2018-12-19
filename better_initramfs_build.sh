#!/bin/sh
epoch=`date +%s`

# Sanity Check: Test if the script runs as root
if [ "$(whoami)" != root ]
then
	echo -e "\nPlease run this script as root! Exiting.\n" >&2
        exit 1
fi

argcount=1
usage="no_re_download_git_repo"
test "$#" -gt "${argcount}" && { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

no_re_download_git_repo="${1-0}"	#0 means we re-download the git repo

mount | grep /boot || { echo "it does not appear that /boot is mounted, maybe we are in a chroot. You have 5 sec to cancel." ; sleep 5 ; }

if [[ -d '/usr/src/linux/.git' ]];
then
    kernel_version=`git -C /usr/src/linux describe --always --tag`
    kernel_commit=`git -C /usr/src/linux rev-parse HEAD`
    initramfs_name="initramfs-${kernel_version}_${kernel_commit}.img"
else
    kernel_version=`readlink -f /usr/src/linux | cut -d '/' -f4`
    initramfs_name="initramfs-${kernel_version}.img"
fi


cd /root || exit 1

if [ "${no_re_download_git_repo}" == 0 ];
then
	echo "about to re-download the git repo"
    sleep 5
	mv better-initramfs better-initramfs."${epoch}"
	git clone https://github.com/jakeogh/better-initramfs.git || exit 1
	mkdir -p /root/better-initramfs/sourceroot/bin || exit 1
fi

cd /root/better-initramfs || exit 1

echo "running bootstrap-all"

bootstrap/bootstrap-all || exit 1 	#builds aborginal

make prepare || exit 1 			#makes filesystem

echo "after make prepare, entering bash"
/bin/bash

mkdir /root/better-initramfs/sourceroot/lib64
cp -ar /lib64/modules /root/better-initramfs/sourceroot/lib64

make image || exit 1			#makes image

#mv -vi /boot/"${initramfs_name}" /boot/"${initramfs_name}"."${epoch}" #dont exit on error because this could be the first time

test -e /boot/"${initramfs_name}" && { echo "moving /boot/${initramfs_name} to /boot/${initramfs_name}.${epoch}" ; mv -vi /boot/"${initramfs_name}" /boot/"${initramfs_name}"."${epoch}" ; }

echo "copying /better-initramfs/output/initramfs.cpio.gz to /boot/${initramfs_name}"
cp -vi /root/better-initramfs/output/initramfs.cpio.gz /boot/"${initramfs_name}"

ls -al /boot/"${initramfs_name}" || exit 1

test -e /boot/initramfs && rm /boot/initramfs  #removing the symlink
ln -r -s /boot/"${initramfs_name}" /boot/initramfs

#ln -s -r /boot/vmlinuz-"${kernel_version}" /boot/vmlinuz

ls -alt /boot

echo "ok, now manually construct a custom initrd and save the steps"
/bin/bash

#cp /boot/grub/grub.cfg /boot/grub/grub.cfg."${epoch}"
#cp /root/cfg/setup/gentoo_installer/grub.cfg /boot/grub/grub.cfg


#wget https://github.com/jakeogh/better-initramfs/archive/master.tar.gz #does not include .git, so make prepare fails with 'not under git?'
#tar xvf master.tar.gz || exit 1
#mv better-initramfs-master better-initramfs
