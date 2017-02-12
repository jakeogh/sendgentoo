#!/bin/sh

./install_gentoo.sh /dev/sda \
 --force \
 --boot-device /dev/sda \
 --boot-device-partition-table gpt \
 --root-device-partition-table gpt \
 --boot-filesystem zfs \
 --root-filesystem zfs \
 --c-std-lib glibc \
 --hostname glibc64gbzfsboot \
 --march nocona \
 --raid disk \
 --raid-group-size 1

