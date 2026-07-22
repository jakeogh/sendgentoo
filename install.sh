#!/bin/bash

if [ "$(whoami)" != root ]
then
    echo -e "\nPlease run this script as root! Exiting.\n" >&2
    exit 1
fi

echo 2 > /sys/module/hid_apple/parameters/fnmode

kwriteconfig5 --file kscreenlockerrc --group Daemon --key Autolock false
qdbus org.freedesktop.ScreenSaver /ScreenSaver configure

kwriteconfig5 --file ~/.config/powermanagementprofilesrc --group AC --group DimDisplay --key idleTime --delete
kwriteconfig5 --file ~/.config/powermanagementprofilesrc --group AC --group DPMSControl --key idleTime --delete
qdbus org.freedesktop.PowerManagement /org/kde/Solid/PowerManagement org.kde.Solid.PowerManagement.reparseConfiguration
qdbus org.freedesktop.PowerManagement /org/kde/Solid/PowerManagement org.kde.Solid.PowerManagement.refreshStatus

passwd gentoo
passwd
nmcli device disconnect enp12s0u9u3c2
date
chronyd -q
date
emerge --sync
nmcli device disconnect enp12s0u9u3c2
emerge xrandr
xrandr -s 1024x768
eselect repository add jakeogh git https://github.com/jakeogh/jakeogh
emerge --sync
emerge portage -1 -u
CONFIG_PROTECT="-*" emerge --autounmask --autounmask-write --autounmask-continue sendgentoo
sendgentoosimple --help
echo "sendgentoosimple --configure-kernel --hostname fastbox --ip 192.168.222.109/24 --disk-size 1.82 /dev/sda"
