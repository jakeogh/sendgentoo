#!/bin/sh

./install_gentoo.sh --force --boot-device /dev/sdc --root-device /dev/sdd --boot-device-partition-table gpt --root-device-partition-table zfs --boot-filesystem ext4 --root-filesystem zfs --c-std-lib glibc --hostname glibc64gbusb --march nocona

