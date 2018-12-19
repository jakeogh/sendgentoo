#!/bin/bash

echo -n "post_chroot.sh args: "
echo "$@"
argcount=6
usage="stdlib boot_device hostname cflags root_filesystem newpasswd"
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
boot_device="${1}"
shift
hostname="${1}"
shift
cflags="${1}"
shift
root_filesystem="${1}"
shift
newpasswd="${1}"
shift

zfs_module_mode="module"
env-update || exit 1
source /etc/profile || exit 1
export PS1="(chroot) $PS1"

#here down is stuff that might not need to run every time
# ---- begin run once, critical stuff ----

echo "root:$newpasswd" | chpasswd
chmod +x /home/cfg/sysskel/etc/local.d/*
echo "PYTHON_TARGETS=\"python2_7 python3_6\"" >> /etc/portage/make.conf
echo "PYTHON_SINGLE_TARGET=\"python3_6\"" >> /etc/portage/make.conf
eselect python set --python3 python3.6 || exit 1
eselect python set python3.6 || exit 1
eselect python list
eselect profile list

echo "hostname=\"${hostname}\"" > /etc/conf.d/hostname
grep -E "^en_US.UTF-8 UTF-8" /etc/locale.gen || { echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen ; }
locale-gen    #hm, musl does not need this? dont fail here for uclibc or musl
grep -E '''^LC_COLLATE="C"''' /etc/env.d/02collate || { echo "LC_COLLATE=\"C\"" >> /etc/env.d/02collate ; }
echo "US/Arizona" > /etc/timezone || exit 1 # not /etc/localtime, the next line does that
emerge --config timezone-data || exit 1

cores=`grep processor /proc/cpuinfo | wc -l`
echo "MAKEOPTS=\"-j${cores}\"" > /etc/portage/makeopts.conf

if [[ "${cflags}" == "native" ]];
then
    echo "CFLAGS=\"-march=native -O2 -pipe -ggdb\"" > /etc/portage/cflags.conf
    echo "CXXFLAGS=\"\${CFLAGS}\"" >> /etc/portage/cflags.conf
elif [[ "${cflags}" == "nocona" ]]; # first x86_64 arch
then
    echo "CFLAGS=\"-march=nocona -O2 -pipe -ggdb\"" > /etc/portage/cflags.conf
    echo "CXXFLAGS=\"\${CFLAGS}\"" >> /etc/portage/cflags.conf
else
    echo "Unknown cflags: ${cflags}"
    exit 1
fi

# right here, portage needs to get configured... this stuff ends up at the end of the final make.conf
echo "ACCEPT_KEYWORDS=\"~amd64\"" >> /etc/portage/make.conf
echo "EMERGE_DEFAULT_OPTS=\"--quiet-build=y --tree --nospinner\"" >> /etc/portage/make.conf
echo "FEATURES=\"parallel-fetch splitdebug buildpkg\"" >> /etc/portage/make.conf

echo "sys-devel/gcc fortran" > /etc/portage/package.use/gcc #otherwise gcc compiles twice

source /etc/profile

#install kernel and update symlink (via use flag)
export KCONFIG_OVERWRITECONFIG=1 # https://www.mail-archive.com/lede-dev@lists.infradead.org/msg07290.html
install_pkg gentoo-sources || exit 1
#mv /usr/src/linux/.config /usr/src/linux/.config.orig # gentoo-sources was jut emerged, so there is no .config yet
mkdir /usr/src/linux_configs
rm /usr/src/linux/.config           # shouldnt exist yet
rm /usr/src/linux_configs/.config   # shouldnt exist yet
test -h /usr/src/linux/.config || ln -s /home/cfg/sysskel/usr/src/linux_configs/.config /usr/src/linux_configs/.config
test -h /usr/src/linux/.config || ln -s /usr/src/linux_configs/.config /usr/src/linux/.config
#cp /usr/src/linux_configs/.config /usr/src/linux/.config
cores=`grep processor /proc/cpuinfo | wc -l`
grep "CONFIG_TRIM_UNUSED_KSYMS is not set" /usr/src/linux/.config || { echo "Rebuild the kernel with CONFIG_TRIM_UNUSED_KSYMS must be =n" ; exit 1 ; }
grep "CONFIG_FB_EFI is not set" /usr/src/linux/.config && { echo "Rebuild the kernel with CONFIG_FB_EFI=y" ; exit 1 ; }

echo "=sys-kernel/spl-9999 **"  >> /etc/portage/package.accept_keywords
echo "=sys-fs/zfs-9999 **"      >> /etc/portage/package.accept_keywords
echo "=sys-fs/zfs-kmod-9999 **" >> /etc/portage/package.accept_keywords

if [[ "${zfs_module_mode}" == "module" ]];
then
    #cd /usr/src/linux && make menuconfig && make -j"${cores}" && make install && make modules_install || exit 1
    cd /usr/src/linux && make oldconfig && make -j"${cores}" && make install && make modules_install || exit 1
    #USE="${USE} -kernel-builtin" emerge zfs zfs-kmod
else
    cd /usr/src/linux && make prepare || exit 1
    #cd /usr/src/linux && make -j"${cores}" && make install && make modules_install || exit 1
    grep "CONFIG_ZFS=y" /usr/src/linux/.config || { echo "1 why did grep \"CONFIG_ZFS=y\" /usr/src/linux/.config exit 1?" ; }
    grep "CONFIG_SPL=y" /usr/src/linux/.config || { echo "1 why did grep \"CONFIG_SPL=y\" /usr/src/linux/.config exit 1?" ; }

    env EXTRA_ECONF='--enable-linux-builtin' ebuild /usr/portage/sys-kernel/spl/spl-9999.ebuild clean configure || exit 1
    #(cd /var/tmp/portage/sys-kernel/spl-9999/work/spl-9999 && ./copy-builtin /usr/src/linux) || exit 1
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

fi

install_pkg_force_compile zfs || exit 1
install_pkg_force_compile zfs-kmod || exit 1
rc-update add zfs-mount boot || exit 1
install_pkg gradm #required for gentoo-hardened RBAC

#echo '''GRUB_PLATFORMS="pc efi-32 efi-64"''' >> /etc/portage/make.conf #not sure why needed, but causes probls on musl
#echo '''GRUB_PLATFORMS="pc"''' >> /etc/portage/make.conf #not sure why needed, but causes probls on musl
install_pkg grub:2 || exit 1
install_pkg memtest86+ # do before generating grub.conf
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
    grep -E "^GRUB_DEVICE=\"PARTUUID=${partuuid}\"" /etc/default/grub || { echo "GRUB_DEVICE=\"PARTUUID=${partuuid}\"" >> /etc/default/grub ; }
    echo -e 'PARTUUID='`/home/cfg/linux/disk/blkid/PARTUUID_root_device` '\t/' '\text4' '\tnoatime' '\t0' '\t1' >> /etc/fstab
fi

cat /home/cfg/sysskel/etc/fstab.custom >> /etc/fstab
mkdir /mnt/t420s_160GB_intel_ssd_SSDSA2M160G2LE
mkdir /mnt/t420s_256GB_samsung_ssd_S2R5NX0J707260P
mkdir /mnt/t420s_160GB_kingston_ssd_SNM225
mkdir /mnt/t420s_2TB_seagate
mkdir /poolz3_8x5TB_A
mkdir /poolz3_8x2TB_A
mkdir /poolz3_16x3TB_A

ln -sf /proc/self/mounts /etc/mtab
#touch /etc/mtab

echo "\"grub-install --compress=no --target=i386-pc --boot-directory=/boot --recheck ${boot_device}\""
grub-install --compress=no --target=i386-pc --boot-directory=/boot --recheck --no-rs-codes "${boot_device}" || exit 1

echo "\"grub-install --compress=no --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot\""
grub-install --compress=no --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot --removable --recheck --no-rs-codes || exit 1

echo "sys-apps/util-linux static-libs" > /etc/portage/package.use/util-linux    # required for genkernel
install_pkg genkernel
genkernel initramfs --no-clean --no-mountboot --zfs || exit 1

grub-mkconfig -o /boot/grub/grub.cfg || exit 1
grub-mkconfig -o /root/chroot_grub.cfg || exit 1

#test -d /boot/efi/EFI/BOOT || { mkdir /boot/efi/EFI/BOOT || exit 1 ; }
#cp -v /boot/efi/EFI/gentoo/grubx64.efi /boot/efi/EFI/BOOT/BOOTX64.EFI || exit 1 # grub does this via --removable

install_pkg netdate
/home/cfg/time/set_time_via_ntp

install_pkg sys-fs/eudev
touch /run/openrc/softlevel
/etc/init.d/udev --nodeps restart


install_pkg gpm
rc-update add gpm default   #console mouse support

grep noclear /etc/inittab || { /home/cfg/_myapps/replace-text/replace-text "c1:12345:respawn:/sbin/agetty 38400 tty1 linux" "c1:12345:respawn:/sbin/agetty 38400 tty1 linux --noclear" /etc/inittab || exit 1 ; }

#/home/cfg/setup/gentoo_installer/post_chroot_build_initramfs


echo "post_chroot.sh is done, exiting 0"
exit 0

#stuff below can happen on reboot

source /etc/profile
emerge --oneshot sys-devel/libtool
emerge world --newuse  # this could upgrade gcc and take a long time
gcc-config 2

emerge @preserved-rebuild
perl-cleaner --all


#install_pkg layman
#cat /etc/layman/layman.cfg | grep -v check_official > /etc/layman/layman.cfg.new
#mv /etc/layman/layman.cfg.new /etc/layman/layman.cfg
#echo "check_official : No" >> /etc/layman/layman.cfg
#layman -L || { /bin/sh ; exit 1 ; }  # get layman trees
#layman -o https://raw.githubusercontent.com/jakeogh/jakeogh/master/jakeogh.xml -f -a jakeogh
#layman -S # update layman trees

install_pkg app-eselect/eselect-repository
eselect repository add jakeogh https://raw.githubusercontent.com/jakeogh/jakeogh/master/jakeogh.xml
install_pkg layman
layman -S # update layman trees

#emerge -u -1 sandbox #why? fails... 
emerge -u -1 portage

install_pkg psutil #hm temp
install_pkg kcl

install_pkg dev-db/redis
#ln -s /home/cfg/sysskel/etc/conf.d/redis redis # symlink_tree does this below
rc-update add redis default


chmod +x /home/cfg/setup/symlink_tree #this depends on kcl
/home/cfg/setup/symlink_tree /home/cfg/sysskel/ || exit 1

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

install_pkg dev-vcs/git # need this for any -9999 packages (zfs)
emerge @preserved-rebuild # good spot to do this as a bunch of flags just changed
emerge @world --quiet-build=y --newuse --changed-use --usepkg=n


test -d /home/user || { useradd --create-home user || exit 1 ; }
echo "user:$newpasswd" | chpasswd || exit 1
for x in cdrom cdrw usb audio plugdev video wheel; do gpasswd -a user $x ; done
/home/cfg/setup/fix_cfg_perms #must happen when user exists

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

mkdir /mnt/sda1 /mnt/sda2 /mnt/sda3 /mnt/sda4 /mnt/sda5 /mnt/sda6
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

install_pkg unison
#ln -s /usr/bin/unison-2.48 /usr/bin/unison
eselect unison list #todo

if [[ "${stdlib}" == "musl" ]];
then
    install_pkg argp-standalone #for musl
fi

install_pkg dnsmasq
mkdir /etc/dnsmasq.d
rc-update add dnsmasq default

install_pkg dnsproxy
rc-update add dnsproxy default

install_pkg eix
chown portage:portage /var/cache/eix
eix-update


install_pkg gpgmda
#emerge --onlydeps --quiet --tree --usepkg=n -u --ask n -n gpgmda
chown root:mail /var/spool/mail/ #invalid group
chmod 03775 /var/spool/mail/

pg_version=`/home/cfg/postgresql/get_version`
rc-update add "postgresql-${pg_version}" default
emerge --config dev-db/postgresql:"${pg_version}"

perl-cleaner modules # needed to avoid XML::Parser... configure: error
perl-cleaner --reallyall

#sudo su postgres -c "psql template1 -c 'create extension hstore;'"
#sudo su postgres -c "psql -U postgres -c 'create extension adminpack;'" #makes pgadmin happy
##sudo su postgres -c "psql template1 -c 'create extension uint;'"

emerge @laptopbase -pv  # https://dev.gentoo.org/~zmedico/portage/doc/ch02.html
emerge @laptopbase

# forever compile time
#install_pkg app-text/pandoc #doc processing, txt to pdf and everything else under the sun

#lspci | grep -i nvidia | grep -i vga && install_pkg sys-firmware/nvidia-firmware #make sure this is after installing sys-apps/pciutils
install_pkg sys-firmware/nvidia-firmware #make sure this is after installing sys-apps/pciutils

#echo "vm.overcommit_memory=2"   >> /etc/sysctl.conf
#echo "vm.overcommit_ratio=100"  >> /etc/sysctl.conf
mkdir /sys/fs/cgroup/memory/0
#echo -e '''#!/bin/sh\necho 1 > /sys/fs/cgroup/memory/0/memory.oom_control''' > /etc/local.d/memory.oom_control.start #done in sysskel
#chmod +x /etc/local.d/memory.oom_control.start

install_pkg alsa-utils #alsamixer
rc-update add alsasound boot
install_pkg media-plugins/alsaequal


if [[ -d '/usr/src/linux/.git' ]];
then
    kernel_version=`git -C /usr/src/linux describe --always --tag`
else
    kernel_version=`readlink -f /usr/src/linux | cut -d '/' -f4 | cut -d '-' -f 2-`
fi

test -e /boot/vmlinuz && { echo "removing old vmlinuz symlink" ; rm /boot/vmlinuz ; }
ls -al /boot/vmlinuz-"${kernel_version}"
ln -s -r /boot/vmlinuz-"${kernel_version}" /boot/vmlinuz

/home/cfg/git/configure_git_global

source /home/cfg/setup/gentoo_installer/install_xorg.sh
install_xorg

