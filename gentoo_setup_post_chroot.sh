#!/bin/bash
argcount=5
usage="stdlib boot_device hostname cflags root_filesystem"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" && exit 1 ; }

#musl: http://distfiles.gentoo.org/experimental/amd64/musl/HOWTO

install_pkg_force_compile()
{
        echo -e "\ninstall_pkg_force_compile() got args: $@" > /dev/stderr
        emerge -pv     --tree --usepkg=n -u --ask n -n $@ > /dev/stderr
        emerge --quiet --tree --usepkg=n -u --ask n -n $@ > /dev/stderr || exit 1
}

install_pkg()
{
        echo -e "\ninstall_pkg() got args: $@" > /dev/stderr
        emerge -pv     --tree --usepkg    -u --ask n -n $@ > /dev/stderr
        emerge --quiet --tree --usepkg    -u --ask n -n $@ > /dev/stderr || exit 1
}

emerge_world()
{
        echo "emerge_world()" > /dev/stderr
        emerge -pv     --backtrack=130 --usepkg --tree -u --ask n -n world > /dev/stderr
        emerge --quiet --backtrack=130 --usepkg --tree -u --ask n -n world > /dev/stderr || exit 1
}

queue_emerge()
{
    echo "entering queue_emerge()" > /dev/stderr
        echo "adding ${@} to world"
        while [ $# -gt 0 ]
        do
            inpkg="${1}"
            pkg=`eix -e# "${inpkg}"`
            #emerge -puv "${pkg}"
            #emerge -puv "${pkg}" | grep "^\[ebuild" | grep "${pkg}"
            exit_status="$?"
            if [[ "${exit_status}" == 0 ]];
            then
                echo "adding to /var/lib/portage/world: ${pkg}"
                grep "${pkg}" /var/lib/portage/world > /dev/null 2>&1 || { echo "${pkg}" >> /var/lib/portage/world ; }
            else
                echo "${pkg} failed"
            fi
            emerge -pv --usepkg --tree -u --ask n -n world
            exit_status="$?"
            if [[ "${exit_status}" != 0 ]];
            then
                echo "emerge world failed on ${pkg}"
                exit 1
            fi
        shift
        done
}

install_xorg()
{
    install_pkg xf86-input-mouse   # works with mdev
    install_pkg xf86-input-evdev   # mouse/kbd for eudev
    #install_pkg slock #Setting caps 'cap_dac_override,cap_setgid,cap_setuid,cap_sys_resource=ep' on file '/usr/bin/slock' failed usage: filecap
    install_pkg xterm xlsfonts xfontsel xfd xtitle lsx xbindkeys
    #install_pkg xorg-x11 #isnt this a dep?
    install_pkg redshift xdpyinfo wmctrl
    install_pkg x11-misc/xclip xev mesa-progs xdotool
    install_pkg dmenu
    install_pkg xbindkeys xautomation xvkbd xsel
    install_pkg xnee xkeycaps
    install_pkg xfontsel terminus-font xlsfonts liberation-fonts
    install_pkg xfd lsw
#    install_pkg sympy #boost craps # failed to create symbolic link '/var/tmp/portage/dev-libs/boost-1.63.0/temp/libpython2.7.so': Permission denied # ERROR: dev-libs/boost-1.63.0::gentoo failed (install phase)
    install_pkg gv
    install_pkg xclock
    install_pkg xpyb
    install_pkg python-xlib
    install_pkg qtile
    install_pkg feh
    #install_pkg gimp #angry about PYTHON_SINGLE_TARGET not being 2.7
    install_pkg app-misc/evtest              #better than xev
    install_pkg kde-misc/kdiff3
    install_pkg x11-misc/vdpauinfo
    install_pkg app-admin/keepassx
    #install_pkg_force_compile exiv2 #temp to fix imagemagic
    install_pkg media-gfx/imagemagick #not linking
    install_pkg sci-electronics/xoscope
    install_pkg app-emulation/qemu
    #install_pkg virt-manager
    #install_pkg app-emulation/virt-viewer #unhappy about PYTHON_SINGLE_TARGET being 3.4
    install_pkg iridb
    install_pkg mpv
    install_pkg youtube-dl
    install_pkg app-text/pdftk
    install_pkg app-mobilephone/dfu-util #to flash bootloaders
    install_pkg net-misc/tigervnc

    #CAN Bus Stuff
    install_pkg net-misc/socketcand
    install_pkg cantoolz
    #install_pkg net-misc/caringcaribou
    #busmaster
    install_pkg pulseview #logic analyzer
    install_pkg sys-firmware/sigrok-firmware-fx2lafw
    install_pkg gqrx
    emerge_world
}

stdlib="${1}"
shift
boot_device="${1}"
shift
hostname="${1}"
shift
cflags="${1}"
shift
root_filesystem="${1}"
shift

zfs_module_mode="module"

timestamp=`date +%s`
echo "calling: source /etc/profile"
source /etc/profile
export PS1="(chroot) $PS1"
echo "setting passwd inside new chroot"
echo "root:cayenneground~__" | chpasswd

echo "chmod +x /home/cfg/sysskel/etc/local.d/*"
chmod +x /home/cfg/sysskel/etc/local.d/*

eselect python set --python3 python3.4
eselect python set python3.4
eselect python list
eselect profile list

mkdir /poolz3_8x5TB_A
#mkdir /etc/portage/repos.conf #make this is layman is getting installed or not
#install_pkg net-misc/curl #only needed with custom FETCHCOMMAND

echo "hostname=\"${hostname}\"" > /etc/conf.d/hostname
env-update && source /etc/profile || exit 1
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen    #hm, musl does not need this? dont fail here for uclibc or musl
echo "LC_COLLATE=\"C\"" >> /etc/env.d/02collate
echo "US/Arizona" > /etc/timezone # not /etc/localtime, the next line does that
emerge --config timezone-data

cores=`grep processor /proc/cpuinfo | wc -l`
echo "MAKEOPTS=\"-j${cores}\"" > /etc/portage/makeopts.conf

if [[ "${cflags}" == "native" ]];
then
    echo "CFLAGS=\"-march=native -O2 -pipe -fomit-frame-pointer -ggdb\"" > /etc/portage/cflags.conf
    echo "CXXFLAGS=\"\${CFLAGS}\"" >> /etc/portage/cflags.conf
elif [[ "${cflags}" == "nocona" ]]; # first x86_64 arch
then
    echo "CFLAGS=\"-march=nocona -O2 -pipe -fomit-frame-pointer -ggdb\"" > /etc/portage/cflags.conf
    echo "CXXFLAGS=\"\${CFLAGS}\"" >> /etc/portage/cflags.conf
else
    echo "Unknown cflags: ${cflags}"
    exit 1
fi

# right here, portage needs to get configured... seems this stuff end sup at the end of the final make.conf
echo "ACCEPT_KEYWORDS=\"~amd64\"" >> /etc/portage/make.conf
echo "EMERGE_DEFAULT_OPTS=\"--quiet-build=y --tree --nospinner\"" >> /etc/portage/make.conf
echo "FEATURES=\"parallel-fetch splitdebug buildpkg\"" >> /etc/portage/make.conf


echo "<=app-portage/layman-2.0.0-r3" >> /etc/portage/package.mask/layman
#equery depgraph layman
#sleep 10
#echo "USE=\"$USE -pcre\"" >> /etc/portage/make.conf #todo fix later. perl sux
#echo "USE=\"$USE -perl\"" >> /etc/portage/make.conf #todo fix later. perl sux
gcc-config x86_64-pc-linux-gnu-5.4.0 || exit 1
source /etc/profile
emerge --oneshot sys-devel/libtool
emerge world --newuse

#emerge -1 --usepkg=n dev-libs/icu
emerge @preserved-rebuild
perl-cleaner --all
emerge layman --usepkg --tree --backtrack=130 --verbose-conflicts  # pulls in git

cat /etc/layman/layman.cfg | grep -v check_official > /etc/layman/layman.cfg.new
mv /etc/layman/layman.cfg.new /etc/layman/layman.cfg

echo "check_official : No" >> /etc/layman/layman.cfg
layman -L || { /bin/sh ; exit 1 ; }  # get layman trees
layman -o https://raw.githubusercontent.com/jakeogh/jakeogh/master/jakeogh.xml -f -a jakeogh

#echo "=dev-python/kcl-0.0.1 ~amd64" >> /etc/portage/package.accept_keywords
install_pkg psutil #hm temp
install_pkg_force_compile kcl #seems the binary didnt pull the deps?

chmod +x /home/cfg/setup/symlink_tree #this depends on kcl
/home/cfg/setup/symlink_tree /home/cfg/sysskel/ || exit 1
/home/cfg/git/configure_git_global

#bug way too late but depends on replace-text which depends on kcl which depends on layman
#if musl is getting used, CHOST must be changed #bug, this is needs to split into it's own conf
if [[ "${stdlib}" == "musl" ]];
then
    echo "setting CHOST to x86_64-gentoo-linux-musl"
    /home/cfg/_myapps/replace-text/replace-text 'CHOST="x86_64-pc-linux-gnu"' 'CHOST="x86_64-gentoo-linux-musl"' /etc/portage/make.conf
elif [[ "${stdlib}" == "uclibc" ]];
then
    echo "setting CHOST to x86_64-gentoo-linux-uclibc"
    /home/cfg/_myapps/replace-text/replace-text 'CHOST="x86_64-pc-linux-gnu"' 'CHOST="x86_64-gentoo-linux-uclibc"' /etc/portage/make.conf
elif [[ "${stdlib}" == "glibc" ]];
then
    echo -n "leaving CHOST as is: "
    grep x86_64-pc-linux-gnu /etc/portage/make.conf || { echo "x86_64-pc-linux-gnu not found in /etc/portage/make.conf, but glibc = ${glibc}, exiting." ; exit 1 ; }
else
    echo "unknown glibc: ${glibc}, exiting."
    exit 1
fi

if [[ "${stdlib}" == "musl" ]];
then
    layman -a musl || exit 1
    echo "source /var/lib/layman/make.conf" >> /etc/portage/make.conf # musl specific # need to switch to repos.d https://wiki.gentoo.org/wiki/Overlay
fi

install_pkg dev-vcs/git # need this for any -9999 packages (zfs)
emerge @preserved-rebuild # good spot to do this as a bunch of flags just changed
emerge @world --newuse --usepkg

#install kernel and update symlink (via use flag)
install_pkg --quiet-build=n hardened-sources || exit 1
#mv /usr/src/linux/.config /usr/src/linux/.config.orig # hardened-sources was jut emerged, so there is no .config yet
test -h /usr/src/linux/.config || ln -s /usr/src/linux_configs/.config /usr/src/linux/.config
#/bin/sh
#cp /usr/src/linux_configs/.config /usr/src/linux/.config
cores=`grep processor /proc/cpuinfo | wc -l`
grep "CONFIG_TRIM_UNUSED_KSYMS is not set" /usr/src/linux/.config || { echo "Rebuild the kernel with CONFIG_TRIM_UNUSED_KSYMS must be =n" ; exit 1 ; }
grep "CONFIG_FB_EFI is not set" /usr/src/linux/.config && { echo "Rebuild the kernel with CONFIG_FB_EFI=y" ; exit 1 ; }


if [[ "${zfs_module_mode}" == "module" ]];
then
    #cd /usr/src/linux && make menuconfig && make -j"${cores}" && make install && make modules_install || exit 1
    cd /usr/src/linux && make oldconfig && make -j"${cores}" && make install && make modules_install || exit 1
    #USE="${USE} -kernel-builtin" emerge spl zfs zfs-kmod
else
    cd /usr/src/linux && make prepare || exit 1
    #cd /usr/src/linux && make -j"${cores}" && make install && make modules_install || exit 1
    grep "CONFIG_ZFS=y" /usr/src/linux/.config || { echo "1 why did grep \"CONFIG_ZFS=y\" /usr/src/linux/.config exit 1?" ; }
    grep "CONFIG_SPL=y" /usr/src/linux/.config || { echo "1 why did grep \"CONFIG_SPL=y\" /usr/src/linux/.config exit 1?" ; }

    env EXTRA_ECONF='--enable-linux-builtin' ebuild /usr/portage/sys-kernel/spl/spl-9999.ebuild clean configure || exit 1
    (cd /var/tmp/portage/sys-kernel/spl-9999/work/spl-9999 && ./copy-builtin /usr/src/linux) || exit 1
    env EXTRA_ECONF='--with-spl=/usr/src/linux --enable-linux-builtin --with-spl-obj=/usr/src/linux' ebuild /usr/portage/sys-fs/zfs-kmod/zfs-kmod-9999.ebuild clean configure || exit 1
    (cd /var/tmp/portage/sys-fs/zfs-kmod-9999/work/zfs-kmod-9999/ && ./copy-builtin /usr/src/linux) || exit 1

    #mkdir -p /etc/portage/profile
    #echo 'sys-fs/zfs -kernel-builtin' >> /etc/portage/profile/package.use.mask
    #echo 'sys-fs/zfs kernel-builtin' >> /etc/portage/package.use/zfs.conf

    grep "CONFIG_SPL=y" /usr/src/linux/.config || echo "CONFIG_SPL=y" >> /usr/src/linux/.config
    grep "CONFIG_ZFS=y" /usr/src/linux/.config || echo "CONFIG_ZFS=y" >> /usr/src/linux/.config

    grep "CONFIG_ZFS=y" /usr/src/linux/.config || { echo "why did grep \"CONFIG_ZFS=y\" /usr/src/linux/.config exit 1?" ; }
    grep "CONFIG_SPL=y" /usr/src/linux/.config || { echo "why did grep \"CONFIG_SPL=y\" /usr/src/linux/.config exit 1?" ; }
    /bin/sh

    cd /usr/src/linux && make -j"${cores}" && make install && make modules_install || exit 1 # again to build-in zfs

    #emerge --oneshot --verbose sys-fs/zfs
    #rc-update add zfs boot  #for zfs on root # not needed if zfs is built-in
    # USE="${USE} -kernel-builtin" emerge spl zfs zfs-kmod || exit 1
fi

install_pkg_force_compile spl || exit 1
install_pkg_force_compile zfs || exit 1
install_pkg_force_compile zfs-kmod || exit 1
rc-update add zfs-mount boot || exit 1
install_pkg gradm #required for gentoo-hardened RBAC

#echo '''GRUB_PLATFORMS="pc efi-32 efi-64"''' >> /etc/portage/make.conf #not sure why needed, but causes probls on musl
#echo '''GRUB_PLATFORMS="pc"''' >> /etc/portage/make.conf #not sure why needed, but causes probls on musl
install_pkg grub:2 || exit 1
install_pkg hexedit
#echo '''USE="$USE device-mapper"'''        >> /etc/portage/make.conf

echo -e "#<fs>\t<mountpoint>\t<type>\t<opts>\t<dump/pass>" > /etc/fstab # create empty fstab

if [[ "${root_filesystem}" == "zfs" ]];
then
    echo "GRUB_PRELOAD_MODULES=\"part_gpt zfs\"" >> /etc/default/grub
   #echo "GRUB_CMDLINE_LINUX_DEFAULT=\"boot=zfs root=ZFS=rpool/ROOT\"" >> /etc/default/grub
   #echo "GRUB_CMDLINE_LINUX_DEFAULT=\"boot=zfs\"" >> /etc/default/grub
   #echo "GRUB_DEVICE=\"ZFS=rpool/ROOT/gentoo\"" >> /etc/default/grub
    echo "GRUB_DEVICE=\"ZFS=${hostname}/ROOT/gentoo\"" >> /etc/default/grub
else
    root_partition=`/home/cfg/linux/disk/get_root_device`
    echo "-------------- root_partition: ${root_partition} ---------------------"
    partuuid=`/home/cfg/linux/hardware/disk/blkid/PARTUUID "${root_partition}"`
    echo "GRUB_DEVICE partuuid: ${partuuid}"
    echo "GRUB_DEVICE=\"PARTUUID=${partuuid}\"" >> /etc/default/grub
    echo -e 'PARTUUID='`/home/cfg/linux/disk/blkid/PARTUUID_root_device` '\t/' '\text4' '\tnoatime' '\t0' '\t1' >> /etc/fstab
fi

ln -sf /proc/self/mounts /etc/mtab
#touch /etc/mtab

#echo "grub-probe /"
#grub-probe /
#echo "sleeping 10s, is zfs detected?"
#sleep 10

echo "\"grub-install --compress=no --target=i386-pc --boot-directory=/boot --recheck ${boot_device}\""
grub-install --compress=no --target=i386-pc --boot-directory=/boot --recheck --no-rs-codes "${boot_device}" || exit 1

echo "\"grub-install --compress=no --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot\""
grub-install --compress=no --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot --removable --recheck --no-rs-codes || exit 1

install_pkg genkernel
genkernel initramfs --no-clean --no-mountboot --zfs || exit 1

grub-mkconfig -o /boot/grub/grub.cfg || exit 1
grub-mkconfig -o /root/chroot_grub.cfg || exit 1
#/bin/sh

#test -d /boot/efi/EFI/BOOT || { mkdir /boot/efi/EFI/BOOT || exit 1 ; }
#cp -v /boot/efi/EFI/gentoo/grubx64.efi /boot/efi/EFI/BOOT/BOOTX64.EFI || exit 1 # grub does this via --removable

test -d /home/user || { useradd --create-home user || exit 1 ; }
echo "user:cayenneground~__" | chpasswd || exit 1
for x in cdrom cdrw usb audio video wheel; do gpasswd -a user $x ; done

test -h /home/user/cfg || { ln -s /home/cfg /home/user/cfg || exit 1 ; }
test -h /root/cfg      || { ln -s /home/cfg /root/cfg      || exit 1 ; }

mkdir /delme
mkdir /usr/portage
#emerge-webrsync
#emerge --sync
eselect profile list

rmdir /etc/portage/package.mask
chmod +x /etc/local.d/export_cores.start
/etc/local.d/export_cores.start

mkdir /mnt/sda1 /mnt/sda2 /mnt/sda3
mkdir /mnt/sdb1 /mnt/sdb2 /mnt/sdb3
mkdir /mnt/sdc1 /mnt/sdc2 /mnt/sdc3
mkdir /mnt/sdd1 /mnt/sdd2 /mnt/sdd3
mkdir /mnt/sde1 /mnt/sde2 /mnt/sde3
mkdir /mnt/sdf1 /mnt/sdf2 /mnt/sdf3
mkdir /mnt/sdg1 /mnt/sdg2 /mnt/sdg3
mkdir /mnt/sdh1 /mnt/sdh2 /mnt/sdh3
mkdir /mnt/sdi1 /mnt/sdi2 /mnt/sdi3
mkdir /mnt/sdj1 /mnt/sdj2 /mnt/sdj3
mkdir /mnt/sdk1 /mnt/sdk2 /mnt/sdk3
mkdir /mnt/sdl1 /mnt/sdl2 /mnt/sdl3
mkdir /mnt/sdm1 /mnt/sdm2 /mnt/sdm3
mkdir /mnt/sdn1 /mnt/sdn2 /mnt/sdn3
mkdir /mnt/sdo1 /mnt/sdo2 /mnt/sdo3
mkdir /mnt/xvdi1 /mnt/xvdj1
mkdir /mnt/loop /mnt/samba /mnt/dvd /mnt/cdrom

install_pkg netdate
/home/cfg/time/set_time_via_ntp

install_pkg ccache

install_pkg sys-fs/eudev
touch /run/openrc/softlevel
/etc/init.d/udev --nodeps restart

if [[ "${stdlib}" == "musl" ]];
then
    emerge -puvNDq world
    emerge -puvNDq world --autounmask=n
    emerge -uvNDq world || exit 1 #http://distfiles.gentoo.org/experimental/amd64/musl/HOWTO
fi

rc-update add sshd default
#rc-update del netmount default  #handeled later, dont want dhcpcd running all the time
rc-update add netmount default

install_pkg syslog-ng
rc-update add syslog-ng default

install_pkg dhcpcd
install_pkg cpio    #for better-initramfs


MAKEOPTS="-j1" emerge --usepkg unison
ln -s /usr/bin/unison-2.48 /usr/bin/unison

if [[ "${stdlib}" == "musl" ]];
then
    install_pkg argp-standalone #for musl
fi

install_pkg sys-process/time

install_pkg dnsmasq
mkdir /etc/dnsmasq.d
rc-update add dnsmasq default

install_pkg dnsproxy
rc-update add dnsproxy default

install_pkg eix #setup/linux:install_pkg() needs this
eix-update

install_pkg moreutils # vidir
install_pkg dev-util/strace dev-util/ltrace
install_pkg iw wpa_supplicant
install_pkg linux-firmware
install_pkg htop iotop sudo vim
install_pkg nmap tcpdump
install_pkg pydf
#install_pkg click #python arg parser, should be a dep by now...
install_pkg sys-apps/usbutils # for lsusb
install_pkg psutil # python system info library
install_pkg parted pyparted
install_pkg multipath-tools # unhappy on musl
install_pkg cryptsetup hexedit
install_pkg ncdu app-text/tree
install_pkg dosfstools #mkfs.vfat for uefi partition
install_pkg pv
install_pkg app-crypt/gnupg
install_pkg dev-util/dirdiff
install_pkg tmux app-misc/mc
install_pkg app-portage/gentoolkit #equery
install_pkg sys-apps/smartmontools   #to get HD sn's
install_pkg timer_entropyd  #ssh-keygen
install_pkg hwinfo  # for checking avail kms modes and detecting video cards
install_pkg lshw lsof
install_pkg pfl     # e-file like qpkg for files that are in portage
install_pkg patchutils # combinediff
install_pkg libbsd # strlcpy https://en.wikibooks.org/wiki/C_Programming/C_Reference/nonstandard/strlcpy
install_pkg debugedit
install_pkg gptfdisk #gdisk sgdisk cgdisk
install_pkg sys-block/gpart # partition disaster recovery tool
install_pkg ddrescue dd-rescue
install_pkg python-gnupg
install_pkg vbindiff
install_pkg colordiff
install_pkg app-arch/unrar app-arch/p7zip app-arch/rzip
install_pkg libisoburn # xorriso
install_pkg dev-tcltk/expect # to script gdisk
install_pkg sys-block/di
install_pkg sys-apps/hdparm
install_pkg app-benchmarks/iozone
install_pkg net-dialup/minicom
#install_pkg app-misc/screen #Can't locate Locale/Messages.pm in @INC

#failing
#install_pkg net-wireless/bluez #bluetooth
#install_pkg sys-firmware/bluez-firmware
#install_pkg net-wireless/bluez-hcidump
#install_pkg dev-python/pybluez

install_pkg app-misc/grc #colorizer for cmds
install_pkg sys-power/acpi
install_pkg net-wireless/wireless-tools
install_pkg dev-python/sh
install_pkg net-fs/nfs-utils
install_pkg app-backup/bup
install_pkg net-proxy/sshuttle
install_pkg sys-apps/kexec-tools #kernel crash dumping
#install_pkg links #fails - media-libs/mesa-17.0.3 (Change USE: -vaapi)
install_pkg app-misc/byobu #screen/tmux manager
install_pkg app-admin/ccze # to make ctail(byobu) happy
install_pkg sys-devel/distcc
install_pkg app-cdr/nrg2iso
install_pkg net-ftp/tftp-hpa
#install_pkg dev-python/pudb # nice python debugger (terminal)

#install_pkg gpgmda
chown root:mail /var/spool/mail/
chmod 03775 /var/spool/mail/

install_pkg net-misc/whois
install_pkg www-client/w3m www-client/elinks
install_pkg sys-apps/most
#install_pkg rust
install_pkg sys-fs/simple-mtpfs
#install_pkg sqlalchemy # iridb dep in ebuild
#install_pkg httplib2 # iridb dep in ebuild
install_pkg dev-python/psycopg
perl-cleaner modules # needed to avoid XML::Parser... configure: error
perl-cleaner --reallyall
install_pkg pgadmin3
#echo "this is not supposed to ask for confirmation:"
test -f /var/lib/postgresql/9.6/data/PG_VERSION || emerge --config --ask=n dev-db/postgresql
/etc/init.d/postgresql-9.6 start
sudo su postgres -c "psql template1 -c 'create extension hstore;'"
sudo su postgres -c "psql -U postgres -c 'create extension adminpack;'" #makes pgadmin happy
#sudo su postgres -c "psql template1 -c 'create extension uint;'"
install_pkg pydot
install_pkg subversion
install_pkg paps #txt to pdf
install_pkg ranpwd
install_pkg dnsgate
install_pkg weechat
#install_pkg pylint #broken
install_pkg dev-vcs/tig #text interface for git

# forever compile time
#install_pkg app-text/pandoc #doc processing, txt to pdf and everything else under the sun

#install_pkg dev-python/beautifulsoup # should be a dep
install_pkg app-cdr/cdrtools
#lspci | grep -i nvidia | grep -i vga && install_pkg sys-firmware/nvidia-firmware #make sure this is after installing sys-apps/pciutils
install_pkg sys-firmware/nvidia-firmware #make sure this is after installing sys-apps/pciutils

/home/cfg/_myapps/replace-text/replace-text "c1:12345:respawn:/sbin/agetty 38400 tty1 linux" "c1:12345:respawn:/sbin/agetty 38400 tty1 linux --noclear" /etc/inittab || exit 1

#echo "vm.overcommit_memory=2"   >> /etc/sysctl.conf
#echo "vm.overcommit_ratio=100"  >> /etc/sysctl.conf
mkdir /sys/fs/cgroup/memory/0
#echo -e '''#!/bin/sh\necho 1 > /sys/fs/cgroup/memory/0/memory.oom_control''' > /etc/local.d/memory.oom_control.start #done in sysskel
#chmod +x /etc/local.d/memory.oom_control.start

install_pkg gpm
rc-update add gpm default   #console mouse support

install_pkg alsa-utils #alsamixer
rc-update add alsasound boot

# /home/cfg/setup/gentoo_installer/gentoo_setup_post_chroot_build_initramfs

#test -e /boot/grub/grub.cfg && mv /boot/grub/grub.cfg /boot/grub/grub.cfg."${timestamp}"
#cp /home/cfg/setup/gentoo_installer/grub.cfg /boot/grub/grub.cfg || echo "unable to copy grub.cfg!"

if [[ -d '/usr/src/linux/.git' ]];
then
    kernel_version=`git -C /usr/src/linux describe --always --tag`
else
    kernel_version=`readlink -f /usr/src/linux | cut -d '/' -f4 | cut -d '-' -f 2-`
fi

test -e /boot/vmlinuz && { echo "removing old vmlinuz symlink" ; rm /boot/vmlinuz ; }
ls -al /boot/vmlinuz-"${kernel_version}"
ln -s -r /boot/vmlinuz-"${kernel_version}" /boot/vmlinuz

/home/cfg/setup/fix_cfg_perms

mkdir /root/repos
cd /root/repos
git clone https://github.com/mrichar1/clipster.git
cd clipster
cp clipster /usr/local/bin

install_xorg
#install_pkg gqrx

