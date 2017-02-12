#!/bin/sh

./install_gentoo.sh /dev/sdc \
 --force \
 --boot-device /dev/sdc \
 --boot-device-partition-table gpt \
 --root-device-partition-table gpt \
 --boot-filesystem ext4 \
 --root-filesystem ext4 \
 --c-std-lib glibc \
 --hostname glibc64gbusbext4 \
 --march nocona \
 --raid disk \
 --raid-group-size 1


