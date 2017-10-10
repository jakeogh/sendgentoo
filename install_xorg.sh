#!/bin/bash
#argcount=5
#usage="stdlib boot_device hostname cflags root_filesystem"
#test "$#" -eq "${argcount}" || { echo "$0 ${usage}" && exit 1 ; }


install_xorg()
{
    install_pkg_force_compile slock #Setting caps 'cap_dac_override,cap_setgid,cap_setuid,cap_sys_resource=ep' on file '/usr/bin/slock' failed usage: filecap
    install_pkg_force_compile x11-base/xorg-server
    install_pkg_force_compile x11-base/xorg-drivers
    install_pkg xf86-input-evdev  # works with mdev mouse/kbd for eudev
    install_pkg xterm xlsfonts xfontsel xfd xtitle lsx redshift xdpyinfo wmctrl x11-misc/xclip xev mesa-progs xdotool dmenu xbindkeys xautomation xvkbd xsel xnee xkeycaps xfontsel terminus-font xlsfonts liberation-fonts xfd lsw evtest
    install_pkg gv xclock xpyb python-xlib
    install_pkg qtile dev-python/pygobject #temp qtile dep
    install_pkg feh
    install_pkg xmodmap
    install_pkg gimp
    install_pkg kde-misc/kdiff3 x11-misc/vdpauinfo app-admin/keepassx
    install_pkg media-gfx/imagemagick sci-electronics/xoscope app-emulation/qemu
    install_pkg virt-manager
    #install_pkg app-emulation/virt-viewer #unhappy about PYTHON_SINGLE_TARGET being 3.4
    install_pkg iridb
    install_pkg mpv youtube-dl app-text/pdftk
    install_pkg app-mobilephone/dfu-util #to flash bootloaders
    install_pkg net-misc/tigervnc
    install_pkg rdesktop
    install_pkg transmission
    install_pkg ipython
    install_pkg x11-misc/clipster
    install_pkg xinput

    #CAN Bus Stuff
    install_pkg net-misc/socketcand cantoolz
    #install_pkg net-misc/caringcaribou
    #busmaster
    #install_pkg pulseview #logic analyzer
    install_pkg sys-firmware/sigrok-firmware-fx2lafw
    #install_pkg gqrx #fails on gnuradio
    #emerge_world
    install_pkg openoffice-bin
    install_pkg app-text/mupdf
}
