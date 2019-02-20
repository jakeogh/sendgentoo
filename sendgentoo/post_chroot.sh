#!/bin/bash

echo -n "post_chroot.sh args: "
echo "$@"
argcount=7
usage="stdlib boot_device hostname cflags root_filesystem newpasswd ip"
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
install_pkg grub:2 || exit 1

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

grep -E "^GRUB_CMDLINE_LINUX=\"net.ifnames=0\"" /etc/default/grub || { echo "GRUB_CMDLINE_LINUX=\"net.ifnames=0\"" >> /etc/default/grub ; }


install_pkg memtest86+ # do before generating grub.conf
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
echo -e "#<fs>\t<mountpoint>\t<type>\t<opts>\t<dump/pass>" > /etc/fstab # create empty fstab
ln -sf /proc/self/mounts /etc/mtab

echo "\"grub-install --compress=no --target=i386-pc --boot-directory=/boot --recheck ${boot_device}\""
grub-install --compress=no --target=i386-pc --boot-directory=/boot --recheck --no-rs-codes "${boot_device}" || exit 1

echo "\"grub-install --compress=no --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot\""
grub-install --compress=no --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot --removable --recheck --no-rs-codes || exit 1


install_pkg gradm #required for gentoo-hardened RBAC
echo "sys-apps/util-linux static-libs" > /etc/portage/package.use/util-linux    # required for genkernel
install_pkg genkernel
/home/cfg/_myapps/sendgentoo/sendgentoo/kernel_recompile.sh || exit 1
cat /home/cfg/sysskel/etc/fstab.custom >> /etc/fstab

rc-update add zfs-mount boot || exit 1
install_pkg dhcpcd # not in stage3


echo "config_eth0=\"${ip}/24\"" >> /etc/conf.d/net


#grub-mkconfig -o /boot/grub/grub.cfg || exit 1 # kernel_recompile.sh does that
#grub-mkconfig -o /root/chroot_grub.cfg || exit 1  # why?

mkdir /mnt/t420s_160GB_intel_ssd_SSDSA2M160G2LE
mkdir /mnt/t420s_256GB_samsung_ssd_S2R5NX0J707260P
mkdir /mnt/t420s_160GB_kingston_ssd_SNM225
mkdir /mnt/t420s_2TB_seagate
mkdir /poolz3_8x5TB_A
mkdir /poolz3_8x2TB_A
mkdir /poolz3_16x3TB_A

install_pkg netdate
/home/cfg/time/set_time_via_ntp

install_pkg sys-fs/eudev
touch /run/openrc/softlevel
/etc/init.d/udev --nodeps restart

install_pkg gpm
rc-update add gpm default   #console mouse support

#install_pkg elogind
#rc-update add elogind default

install_pkg app-admin/sysklogd
rc-update add sysklogd default  # syslog-ng hangs on boot... bloated


mkdir /etc/portage/package.mask
echo ">net-misc/unison-2.48.4" > /etc/portage/package.mask/unison
install_pkg unison
#ln -s /usr/bin/unison-2.48 /usr/bin/unison
eselect unison list #todo

install_pkg tmux
install_pkg vim
install_pkg dev-db/redis  # later on, fix_cfg_perms will try to use the redis:redis user
install_pkg sudo
install_pkg lsof
install_pkg pydf
install_pkg app-portage/gentoolkit #equery
install_pkg sys-process/htop
install_pkg ddrescue
install_pkg sys-process/vixie-cron
install_pkg net-dns/bind-tools
install_pkg app-admin/sysstat   #mpstat

install_pkg sys-apps/smartmontools
rc-update add smartd default

install_pkg app-eselect/eselect-repository
#eselect repository add jakeogh https://raw.githubusercontent.com/jakeogh/jakeogh/master/jakeogh.xml
install_pkg layman
layman -o "https://raw.githubusercontent.com/jakeogh/jakeogh/master/jakeogh.xml" -f -a jakeogh
layman -S # update layman trees

# must be done after overlay is installed
echo "=dev-python/replace-text-9999 **" >> /etc/portage/package.accept_keywords
install_pkg replace-text
export LANG="C.UTF-8"  # to make click happy
grep noclear /etc/inittab || { replace-text "c1:12345:respawn:/sbin/agetty 38400 tty1 linux" "c1:12345:respawn:/sbin/agetty 38400 tty1 linux --noclear" /etc/inittab || exit 1 ; }
install_pkg sys-apps/moreutils # need sponge for the next command
grep "c7:2345:respawn:/sbin/agetty 38400 tty7 linux" /etc/inittab || { cat /etc/inittab | /home/cfg/text/insert_line_after_match "c6:2345:respawn:/sbin/agetty 38400 tty6 linux" "c7:2345:respawn:/sbin/agetty 38400 tty7 linux" | sponge /etc/inittab ; }

install_pkg sendgentoo # must be done after jakeogh overlay

mkdir /etc/portage/sets
cp /home/cfg/sysskel/etc/portage/sets/laptopbeforereboot /etc/portage/sets/
emerge @laptopbeforereboot -pv
emerge @laptopbeforereboot

echo "chroot_gentoo.sh complete" > /install_status

echo "post_chroot.sh is done, exiting 0"
exit 0

#stuff below can happen on reboot

