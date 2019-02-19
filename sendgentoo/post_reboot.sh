#!/bin/bash

argcount=2
usage="stdlib newpasswd"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" && exit 1 ; }

#musl: http://distfiles.gentoo.org/experimental/amd64/musl/HOWTO
#spark: https://github.com/holman/spark.git

install_pkg_force_compile()
{
        echo -e "\ninstall_pkg_force_compile() got args: $@" > /dev/stderr
        emerge -pv     --tree --usepkg=n -u --ask n -n $@ > /dev/stderr
        emerge --quiet --tree --usepkg=n -u --ask n -n $@ > /dev/stderr || exit 1
}

install_pkg()
{
        echo -e "\ninstall_pkg() got args: $@" > /dev/stderr
        emerge -pv     --tree --usepkg=n    -u --ask n -n $@ > /dev/stderr
        emerge --quiet --tree --usepkg=n    -u --ask n -n $@ > /dev/stderr || exit 1
}

emerge_world()
{
        echo "emerge_world()" > /dev/stderr
        emerge -pv     --backtrack=130 --usepkg=n --tree -u --ask n -n world > /dev/stderr
        emerge --quiet --backtrack=130 --usepkg=n --tree -u --ask n -n world > /dev/stderr || exit 1
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
            emerge -pv --usepkg=n --tree -u --ask n -n world
            exit_status="$?"
            if [[ "${exit_status}" != 0 ]];
            then
                echo "emerge world failed on ${pkg}"
                exit 1
            fi
        shift
        done
}


stdlib="${1}"
shift
newpasswd="${1}"
shift

env-update || exit 1
source /etc/profile || exit 1
export PS1="(chroot) $PS1"

mkdir /delme
mkdir /usr/portage
chown -R portage:portage /usr/portage

/usr/bin/emerge -u --oneshot sys-devel/libtool
#emerge world --newuse  # this could upgrade gcc and take a long time
#gcc-config 2

#emerge @preserved-rebuild
#perl-cleaner --all

emerge -u -1 portage

mkdir /etc/dnsmasq.d
install_pkg dnsmasq
install_pkg dnsproxy

echo "dev-lang/python sqlite" > /etc/portage/package.use/python
echo "media-libs/gd fontconfig jpeg png truetype" > /etc/portage/package.use/gd
install_pkg kcl

chmod +x /home/cfg/setup/symlink_tree #this depends on kcl
/home/cfg/setup/symlink_tree /home/cfg/sysskel/ || exit 1

rc-update add dnsmasq default
rc-update add dnsproxy default
/etc/init.d/dnsmasq start
/etc/init.d/dnsproxy start


#must be done after symlink_tree so etc/skel gets populated
test -d /home/user || { useradd --create-home user || exit 1 ; }
echo "user:$newpasswd" | chpasswd || exit 1

for x in cdrom cdrw usb audio plugdev video wheel; do gpasswd -a user $x ; done

/home/cfg/setup/fix_cfg_perms #must happen when user exists

test -h /home/user/cfg || { ln -s /home/cfg /home/user/cfg || exit 1 ; }
test -h /root/cfg      || { ln -s /home/cfg /root/cfg      || exit 1 ; }
test -h /home/user/_myapps || { ln -s /home/cfg/_myapps /home/user/_myapps || exit 1 ; }
test -h /root/_myapps      || { ln -s /home/cfg/_myapps /root/_myapps      || exit 1 ; }

test -h /home/user/_repos || { ln -s /home/cfg/_repos /home/user/_repos || exit 1 ; }
test -h /root/_repos      || { ln -s /home/cfg/_repos /root/_repos || exit 1 ; }

test -h /home/user/__email_folders || { ln -s /mnt/t420s_160GB_kingston_ssd_SNM225/__email_folders /home/user/__email_folders || exit 1 ; }

touch /home/user/.lesshst
chattr +i /home/user/.lesshst

touch /home/user/.mupdf.history
chattr +i /home/user/.mupdf.history

touch /home/user/.pdfbox.cache
chattr +i /home/user/.pdfbox.cache

# in case the old make.conf is not using the latest python, really the lines should be grabbed from the stock one in the stage 3
echo "PYTHON_TARGETS=\"python2_7 python3_6\"" >> /etc/portage/make.conf
echo "PYTHON_SINGLE_TARGET=\"python3_6\"" >> /etc/portage/make.conf

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

install_pkg cpuid2cpuflags
echo "*/* $(cpuid2cpuflags)" > /etc/portage/package.use/00cpu-flags

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
mkdir /mnt/xvdi1 /mnt/xvdj1
mkdir /mnt/loop /mnt/samba /mnt/dvd /mnt/cdrom

#install_pkg dev-db/redis
##ln -s /home/cfg/sysskel/etc/conf.d/redis redis # symlink_tree does this below
#rc-update add redis default

#install_pkg psutil


if [[ "${stdlib}" == "musl" ]];
then
    install_pkg argp-standalone #for musl
    emerge -puvNDq world
    emerge -puvNDq world --autounmask=n
    emerge -uvNDq world || exit 1 #http://distfiles.gentoo.org/experimental/amd64/musl/HOWTO
fi

rc-update add netmount default
install_pkg syslog-ng
rc-update add syslog-ng default


install_pkg eix
chown portage:portage /var/cache/eix
eix-update

pg_version=`/home/cfg/postgresql/version`
rc-update add "postgresql-${pg_version}" default
emerge --config dev-db/postgresql:"${pg_version}" # didnt work ?

#perl-cleaner modules # needed to avoid XML::Parser... configure: error
#perl-cleaner --reallyall

emerge @laptopbase -pv  # https://dev.gentoo.org/~zmedico/portage/doc/ch02.html
emerge @laptopbase

# forever compile time
#install_pkg app-text/pandoc #doc processing, txt to pdf and everything else under the sun

#lspci | grep -i nvidia | grep -i vga && install_pkg sys-firmware/nvidia-firmware #make sure this is after installing sys-apps/pciutils
install_pkg sys-firmware/nvidia-firmware #make sure this is after installing sys-apps/pciutils

install_pkg alsa-utils #alsamixer
rc-update add alsasound boot
install_pkg media-plugins/alsaequal

if [[ -d '/usr/src/linux/.git' ]];
then
    kernel_version=`git -C /usr/src/linux describe --always --tag`
else
    kernel_version=`readlink -f /usr/src/linux | cut -d '/' -f4 | cut -d '-' -f 2-`
fi

install_pkg gpgmda
chown root:mail /var/spool/mail/ #invalid group
chmod 03775 /var/spool/mail/

emerge @laptopxorg -pv
emerge @laptopxorg

echo "post_chroot.sh complete"

##echo "vm.overcommit_memory=2"   >> /etc/sysctl.conf
##echo "vm.overcommit_ratio=100"  >> /etc/sysctl.conf
#mkdir /sys/fs/cgroup/memory/0
##echo -e '''#!/bin/sh\necho 1 > /sys/fs/cgroup/memory/0/memory.oom_control''' > /etc/local.d/memory.oom_control.start #done in sysskel
##chmod +x /etc/local.d/memory.oom_control.start

#sudo su postgres -c "psql template1 -c 'create extension hstore;'"
#sudo su postgres -c "psql -U postgres -c 'create extension adminpack;'" #makes pgadmin happy
##sudo su postgres -c "psql template1 -c 'create extension uint;'"
