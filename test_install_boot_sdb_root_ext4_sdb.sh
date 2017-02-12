#!/bin/sh

./install_gentoo.sh /dev/sdb \
 --force \
 --boot-device /dev/sdb \
 --boot-device-partition-table gpt \
 --root-device-partition-table gpt \
 --boot-filesystem ext4 \
 --root-filesystem ext4 \
 --c-std-lib glibc \
 --hostname glibc64gbext4boot \
 --march nocona \
 --raid disk \
 --raid-group-size 1

