#!/bin/bash

set -x

argcount=2
usage="stdlib newpasswd"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" && exit 1 ; }

#musl: http://distfiles.gentoo.org/experimental/amd64/musl/HOWTO
#spark: https://github.com/holman/spark.git

source /home/cfg/_myapps/sendgentoo/sendgentoo/utils.sh
#cat /etc/portage/proxy.conf | tr '\n' '\0' | xargs -0 -I '{}' export '{}'
#eval `cat /etc/portage/proxy.conf`
#echo "${http_proxy}"

test -d /delme || { mkdir /delme || exit 1 ; }
chown -R portage:portage /var/db/repos
#chown portage:portage /var/db/repos/gentoo
test -e /etc/portage/proxy.conf || touch /etc/portage/proxy.conf
test -e /etc/portage/cpuflags.conf || touch /etc/portage/cpuflags.conf
grep -E "^source /etc/portage/proxy.conf" /etc/portage/make.conf || echo "source /etc/portage/proxy.conf" >> /etc/portage/make.conf


stdlib="${1}"
shift
newpasswd="${1}"
shift

env-update || exit 1
source /etc/profile || exit 1
#export PS1="(chroot) $PS1"

emerge --sync #|| exit 1  # if post_croot.sh was interrupted, some overlays might not exit
install_pkg tmux || exit 1
install_pkg app-admin/sudo || exit 1

set +u # disable nounset
test -z $TMUX && { echo "start tmux!" ; exit 1 ; }
set -o nounset

install_pkg portage -1 || exit 1
install_pkg unison

install_pkg --oneshot sys-devel/libtool
#emerge world --newuse  # this could upgrade gcc and take a long time
#gcc-config 2

#emerge @preserved-rebuild
#perl-cleaner --all

#mkdir /etc/dnsmasq.d
#install_pkg dnsmasq || exit 1
#install_pkg dnsproxy

install_pkg net-dns/dnscrypt-proxy
rc-update add dnscrypt-proxy default

mkdir /etc/portage/package.use
grep -E "^dev-lang/python sqlite" /etc/portage/package.use/python || { echo "dev-lang/python sqlite" >> /etc/portage/package.use/python ; }  # this is done in post_chroot too...
grep -E "^media-libs/gd fontconfig jpeg png truetype" /etc/portage/package.use/gd || { echo "media-libs/gd fontconfig jpeg png truetype" >> /etc/portage/package.use/gd ; }  # ditto

install_pkg_force symlinktree || exit 1
export LANG="en_US.UTF8"  # to make click happy
symlinktree /home/cfg/sysskel --verbose || exit 1
symlinktree /home/cfg/sysskel --verbose --re-apply-skel /root || exit 1

# done in post_chroot.py
#touch /etc/portage/proxy.conf  # or emerge is really unhappy

/etc/init.d/dnscrypt-proxy start
/home/cfg/linux/gentoo/layman/update_all_overlays
install_pkg debugedit
emerge @world --newuse

#touch /etc/portage/proxy.conf

test -h /root/cfg     || { ln -s /home/cfg /root/cfg             || exit 1 ; }
test -h /root/_myapps || { ln -s /home/cfg/_myapps /root/_myapps || exit 1 ; }
test -h /root/_repos  || { ln -s /home/cfg/_repos /root/_repos   || exit 1 ; }

#rc-update add dnsmasq default
#rc-update add dnsproxy default
#/etc/init.d/dnsmasq start
#/etc/init.d/dnsproxy start

install_pkg cpuid2cpuflags
#echo "*/* $(cpuid2cpuflags)" > /etc/portage/package.use/00cpuflags
echo CPU_FLAGS_X86=$(echo \"$(echo "$(cpuid2cpuflags)" | cut -d ':' -f 2 | sed 's/^[ \t]*//')\") > /etc/portage/cpuflags.conf


install_pkg dodo
install_pkg echocommand
#install_pkg dnsgate
install_pkg_force app-misc/edit
install_pkg net-fs/nfs-utils

echo "MACHINE_SIG=\"`/home/cfg/hardware/make_machine_signature_string`\"" > /etc/env.d/99machine_sig

#must be done after symlink_tree so etc/skel gets populated
test -d /home/user || { useradd --create-home user || exit 1 ; }
#echo "user:$newpasswd" | chpasswd #|| exit 1  # bug https://unix.stackexchange.com/questions/223965/i-cant-change-users-passwd-on-ubuntu
passwd -d user

emerge -1 -u media-libs/libmtp  # creates plugdev group
for x in cdrom cdrw usb audio plugdev video wheel; do gpasswd -a user $x ; done

/home/cfg/setup/fix_cfg_perms #must happen when user exists


immute() {
    rm -f "${1}"
    touch "${1}"
    chattr +i "${1}"
}

# todo /root
immute /home/user/.lesshst
immute /home/user/.mupdf.history
immute /home/user/.pdfbox.cache
immute /home/user/.rediscli_history
immute /home/user/unison.log
immute /home/user/tldextract.cache
immute /home/user/.python_history

test -h /home/user/cfg || { ln -s /home/cfg /home/user/cfg || exit 1 ; }
test -h /home/user/_myapps || { ln -s /home/cfg/_myapps /home/user/_myapps || exit 1 ; }
test -h /home/user/_repos || { ln -s /home/cfg/_repos /home/user/_repos || exit 1 ; }

/home/cfg/git/configure_git_global

#bug way too late but depends on replace-text which depends on kcl which depends on layman
#if musl is getting used, CHOST must be changed #bug, this is needs to split into it's own conf
if [[ "${stdlib}" == "musl" ]];
then
    echo "setting CHOST to x86_64-gentoo-linux-musl"
    /home/cfg/_myapps/replace-text/replace-text --match 'CHOST="x86_64-pc-linux-gnu"' --replacement 'CHOST="x86_64-gentoo-linux-musl"' /etc/portage/make.conf
elif [[ "${stdlib}" == "uclibc" ]];
then
    echo "setting CHOST to x86_64-gentoo-linux-uclibc"
    /home/cfg/_myapps/replace-text/replace-text --match 'CHOST="x86_64-pc-linux-gnu"' --replacement 'CHOST="x86_64-gentoo-linux-uclibc"' /etc/portage/make.conf
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
#emerge @preserved-rebuild # good spot to do this as a bunch of flags just changed
#emerge @world --quiet-build=y --newuse --changed-use --usepkg=n

#emerge-webrsync
#emerge --sync
eselect profile list

#rmdir /etc/portage/package.mask #why?
chmod +x /etc/local.d/export_cores.start
/etc/local.d/export_cores.start

mkdir /mnt/sda1 /mnt/sda2 /mnt/sda3 /mnt/sda4 /mnt/sda5 /mnt/sda6 /mnt/sda7 /mnt/sda8 /mnt/sda9 /mnt/sda10 /mnt/sda11
mkdir /mnt/sdb1 /mnt/sdb2 /mnt/sdb3 /mnt/sdb4 /mnt/sdb5 /mnt/sdb6
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
mkdir /mnt/sdp1 /mnt/sdp2 /mnt/sdp3
mkdir /mnt/sdq1 /mnt/sdq2 /mnt/sdq3
mkdir /mnt/xvdi1 /mnt/xvdj1
mkdir /mnt/loop /mnt/samba /mnt/dvd /mnt/cdrom
mkdir /mnt/smb

if [[ "${stdlib}" == "musl" ]];
then
    install_pkg argp-standalone #for musl
    emerge -puvNDq world
    emerge -puvNDq world --autounmask=n
    emerge -uvNDq world || exit 1 #http://distfiles.gentoo.org/experimental/amd64/musl/HOWTO
fi

rc-update add netmount default

install_pkg eix
chown portage:portage /var/cache/eix
eix-update

install_pkg postgresql
pg_version=`/home/cfg/postgresql/version`
rc-update add "postgresql-${pg_version}" default
emerge --config dev-db/postgresql:"${pg_version}"  # ok to fail if already conf
sudo su postgres -c "psql template1 -c 'create extension hstore;'"
sudo su postgres -c "psql template1 -c 'create extension ltree;'"
install_pkg sshd-configurator
#emerge --depclean  # unmerges partial emerges, do this after install is known good
install_pkg @laptopbase  # https://dev.gentoo.org/~zmedico/portage/doc/ch02.html
install_pkg @wwwsurf
install_pkg @webcam

install_pkg @print
gpasswd -a root lp
gpasswd -a user lp
gpasswd -a root lpadmin
gpasswd -a user lpadmin


#lspci | grep -i nvidia | grep -i vga && install_pkg sys-firmware/nvidia-firmware #make sure this is after installing sys-apps/pciutils
install_pkg sys-firmware/nvidia-firmware #make sure this is after installing sys-apps/pciutils

install_pkg alsa-utils #alsamixer
rc-update add alsasound boot
install_pkg media-plugins/alsaequal
install_pkg media-sound/alsa-tools

if [[ -d '/usr/src/linux/.git' ]];
then
    kernel_version=`git -C /usr/src/linux describe --always --tag`
else
    kernel_version=`readlink -f /usr/src/linux | cut -d '/' -f4 | cut -d '-' -f 2-`
fi

#install_pkg gpgmda
chown root:mail /var/spool/mail/ #invalid group
chmod 03775 /var/spool/mail/


install_pkg @laptopxorg -pv
install_pkg @laptopxorg

install_pkg @gpib -pv
install_pkg @gpib

#eselect repository enable science
#emaint sync -r science
#emerge @gpib -pv
#emerge @gpib
#gpib_config

install_pkg app-editors/neovim && emerge --unmerge vim

echo "post_reboot.sh complete"

##echo "vm.overcommit_memory=2"   >> /etc/sysctl.conf
##echo "vm.overcommit_ratio=100"  >> /etc/sysctl.conf
#mkdir /sys/fs/cgroup/memory/0
##echo -e '''#!/bin/sh\necho 1 > /sys/fs/cgroup/memory/0/memory.oom_control''' > /etc/local.d/memory.oom_control.start #done in sysskel
##chmod +x /etc/local.d/memory.oom_control.start

#sudo su postgres -c "psql template1 -c 'create extension hstore;'"
#sudo su postgres -c "psql -U postgres -c 'create extension adminpack;'" #makes pgadmin happy
##sudo su postgres -c "psql template1 -c 'create extension uint;'"
