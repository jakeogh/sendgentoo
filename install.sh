#!/bin/bash

am_i_root()
{
    if [ "$(whoami)" != root ]
    then
        echo -e "\nPlease run this script as root! Exiting.\n" >&2
        exit 1
    fi
}

am_i_root
#mount | grep gentoo | cut -d ' ' -f 3 | xargs -I '{}' sudo umount '{}'
passwd gentoo
emerge --sync
eselect repository add jakeogh git https://github.com/jakeogh/jakeogh
emerge --sync
CONFIG_PROTECT="-*" emerge --autounmask --autounmask-write --autounmask-continue sendgentoo
sendgentoosimple --help

