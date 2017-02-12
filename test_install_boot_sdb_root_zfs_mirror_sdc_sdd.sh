#!/bin/sh

./install_gentoo.sh /dev/sdc /dev/sdd --force --boot-device /dev/sdb --boot-device-partition-table gpt --root-device-partition-table zfs --boot-filesystem ext4 --root-filesystem zfs --c-std-lib glibc --hostname glibc64gbzfs4gbmirror --march nocona --raid mirror 

