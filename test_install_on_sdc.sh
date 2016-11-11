#!/bin/sh

./install_gentoo.sh --force --boot-device /dev/sdc --root-device /dev/sdc --boot-device-partition-table gpt --root-device-partition-table gpt --boot-filesystem ext4 --root-filesystem ext4 --c-std-lib glibc --hostname glibc64gbusb --march nocona

#./install_gentoo.sh --force --boot-device /dev/sdc --root-device /dev/sdc --boot-device-partition-table gpt --root-device-partition-table gpt --boot-device-filesystem ext4 --root-device-filesystem ext4 --c-std-lib glibc --hostname glibc64gbusb
