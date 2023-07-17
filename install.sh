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
passwd
date
chronyd -q
date
#netdate time.nist.gov
emerge --sync
eselect repository add jakeogh git https://github.com/jakeogh/jakeogh
emerge --sync
emerge portage -1 -u
CONFIG_PROTECT="-*" emerge --autounmask --autounmask-write --autounmask-continue sendgentoo
sendgentoosimple --help
echo "sendgentoosimple --configure --hostname fastbox --ip 192.168.222.109/24 --arch amd64 /dev/sda --disk-size 1.82"
