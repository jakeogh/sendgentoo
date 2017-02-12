#!/bin/sh

./install_gentoo.sh /dev/sda /dev/sdb /dev/sdc /dev/sdd --force \
--boot-device /dev/sda \
--boot-device-partition-table gpt \
--root-device-partition-table gpt \
--boot-filesystem zfs \
--root-filesystem zfs \
--c-std-lib glibc \
--hostname x5680x4raid10 \
--march nocona \
--raid mirror 

