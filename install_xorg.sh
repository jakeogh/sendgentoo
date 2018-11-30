#!/bin/bash
#argcount=5
#usage="stdlib boot_device hostname cflags root_filesystem"
#test "$#" -eq "${argcount}" || { echo "$0 ${usage}" && exit 1 ; }


install_xorg()
{
    emerge @laptopxorg -pv
    emerge @laptopxorg

    #install_pkg_force_compile slock #Setting caps 'cap_dac_override,cap_setgid,cap_setuid,cap_sys_resource=ep' on file '/usr/bin/slock' failed usage: filecap
    #install_pkg_force_compile x11-base/xorg-server
    #install_pkg_force_compile x11-base/xorg-drivers
    #install_pkg xf86-input-evdev  # works with mdev mouse/kbd for eudev
    #install_pkg xterm xlsfonts xfontsel xfd xtitle lsx redshift xdpyinfo wmctrl x11-misc/xclip xev mesa-progs xdotool dmenu xbindkeys xautomation xvkbd xsel xnee xkeycaps xfontsel terminus-font xlsfonts liberation-fonts xfd lsw evtest
    #install_pkg gv xclock
    ##install_pkg xpyb # gone?
    ##install_pkg python-xlib # should be a dep
    #install_pkg qtile # dev-python/pygobject #temp qtile dep
    #install_pkg feh
    #install_pkg xmodmap
    #install_pkg gimp
    ##install_pkg kde-misc/kdiff3 # libressl problem
    #install_pkg x11-misc/vdpauinfo
    #install_pkg app-admin/keepassxc
    #install_pkg media-gfx/imagemagick sci-electronics/xoscope app-emulation/qemu
    #install_pkg virt-manager
    ##install_pkg app-emulation/virt-viewer #unhappy about PYTHON_SINGLE_TARGET being 3.4
    #install_pkg iridb
    #install_pkg mpv
    #install_pkg youtube-dl
    #install_pkg app-text/pdftk
    #install_pkg app-mobilephone/dfu-util #to flash bootloaders
    #install_pkg net-misc/tigervnc
    #install_pkg rdesktop
    #install_pkg transmission
    #install_pkg ipython
    #install_pkg x11-misc/clipster
    #install_pkg xinput
    #install_pkg x11-apps/xwininfo
    #install_pkg audacity

    ##CAN Bus Stuff
    #install_pkg net-misc/socketcand
    ##install_pkg cantoolz # Package installs 'tests' package which is forbidden and likely a bug in the build system.
    ##install_pkg net-misc/caringcaribou
    ##busmaster
    ##install_pkg pulseview #logic analyzer
    #install_pkg sys-firmware/sigrok-firmware-fx2lafw
    ##install_pkg gqrx #fails on gnuradio
    ##emerge_world
    #install_pkg openoffice-bin
    #install_pkg app-text/mupdf
    #install_pkg x11-libs/xosd #osd_cat
    #install_pkg x11-apps/appres
    #install_pkg x11-apps/xrandr #screen rotation
    ##install_pkg sci-chemistry/avogadro #molecule drawing # missing?
    #install_pkg net-wireless/wpa_supplicant
    #install_pkg net-wireless/aircrack-ng
    #install_pkg net-wireless/wifi-radar
    #install_pkg net-wireless/inspectrum #read sdr capture files
    ##install_pkg net-analyzer/wireshark # fails on libssh dep
    #install_pkg cups
    #install_pkg net-print/cups-filters
    #install_pkg net-print/foomatic-db
    #install_pkg net-print/foomatic-db-engine
    #install_pkg net-print/foomatic-db-ppds
    #install_pkg wicd
    #install_pkg dev-db/pgadmin4 # takes forever due to llvm compile # no really... hours 4+
}
