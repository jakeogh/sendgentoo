#!/bin/sh

./umount_mnt_gentoo.sh
./install_gentoo.sh /dev/sda \
 --force \
 --boot-device /dev/sda \
 --boot-device-partition-table gpt \
 --root-device-partition-table gpt \
 --boot-filesystem ext4 \
 --root-filesystem ext4 \
 --c-std-lib glibc \
 --hostname glibc128gbssdext4 \
 --march nocona \
 --raid disk \
 --raid-group-size 1


