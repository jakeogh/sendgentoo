#!/bin/bash
set -o nounset

echo -n "$0 args: "
echo -e "$@\n"
argcount=5
usage="stdlib boot_device cflags root_filesystem newpasswd"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" && exit 1 ; }

set -o nounset
set -x

#musl: http://distfiles.gentoo.org/experimental/amd64/musl/HOWTO
#spark: https://github.com/holman/spark.git

#export https_proxy="http://192.168.222.100:8888"
#export http_proxy="http://192.168.222.100:8888"

source /home/cfg/_myapps/sendgentoo/sendgentoo/utils.sh

stdlib="${1}"  # unused
shift
boot_device="${1}"
shift
cflags="${1}"
shift
root_filesystem="${1}"
shift
newpasswd="${1}"
shift

mount | grep "/boot/efi" || exit 1

emerge --sync

mkdir -p /var/db/repos/gentoo

zfs_module_mode="module"
env-update || exit 1
source /etc/profile || exit 1
#export PS1="(chroot) $PS1"

#here down is stuff that might not need to run every time
# ---- begin run once, critical stuff ----

echo "root:$newpasswd" | chpasswd
chmod +x /home/cfg/sysskel/etc/local.d/*
echo "PYTHON_TARGETS=\"python3_6 python3_7\"" >> /etc/portage/make.conf
echo "PYTHON_SINGLE_TARGET=\"python3_6\"" >> /etc/portage/make.conf
eselect python set --python3 python3.6 || exit 1
eselect python set python3.6 || exit 1
eselect python list
eselect profile list

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
grep "ACCEPT_KEYWORDS=\"~amd64\"" /etc/portage/make.conf || echo "ACCEPT_KEYWORDS=\"~amd64\"" >> /etc/portage/make.conf
grep "EMERGE_DEFAULT_OPTS=\"--quiet-build=y --tree --nospinner\"" /etc/portage/make.conf || \
    echo "EMERGE_DEFAULT_OPTS=\"--quiet-build=y --tree --nospinner\"" >> /etc/portage/make.conf
grep "FEATURES=\"parallel-fetch splitdebug buildpkg\"" /etc/portage/make.conf || \
    echo "FEATURES=\"parallel-fetch splitdebug buildpkg\"" >> /etc/portage/make.conf

echo "sys-devel/gcc fortran" > /etc/portage/package.use/gcc #otherwise gcc compiles twice

source /etc/profile

#install kernel and update symlink (via use flag)
export KCONFIG_OVERWRITECONFIG=1 # https://www.mail-archive.com/lede-dev@lists.infradead.org/msg07290.html
install_pkg gentoo-sources || exit 1
install_pkg grub:2 || exit 1

/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot_install_grub.sh "${boot_device}" || exit 1

#if [[ "${root_filesystem}" == "zfs" ]];
#then
#    echo "GRUB_PRELOAD_MODULES=\"part_gpt part_msdos zfs\"" >> /etc/default/grub
#   #echo "GRUB_CMDLINE_LINUX_DEFAULT=\"boot=zfs root=ZFS=rpool/ROOT\"" >> /etc/default/grub
#   #echo "GRUB_CMDLINE_LINUX_DEFAULT=\"boot=zfs\"" >> /etc/default/grub
#   #echo "GRUB_DEVICE=\"ZFS=rpool/ROOT/gentoo\"" >> /etc/default/grub
#   # echo "GRUB_DEVICE=\"ZFS=${hostname}/ROOT/gentoo\"" >> /etc/default/grub #this was uncommented, disabled to not use hostname
#else
#    echo "GRUB_PRELOAD_MODULES=\"part_gpt part_msdos\"" >> /etc/default/grub
#    root_partition=`/home/cfg/linux/disk/get_root_device`
#    echo "-------------- root_partition: ${root_partition} ---------------------"
#    partuuid=`/home/cfg/linux/hardware/disk/blkid/PARTUUID "${root_partition}"`
#    echo "GRUB_DEVICE partuuid: ${partuuid}"
#    grep -E "^GRUB_DEVICE=\"PARTUUID=${partuuid}\"" /etc/default/grub || { echo "GRUB_DEVICE=\"PARTUUID=${partuuid}\"" >> /etc/default/grub ; }
#    echo -e 'PARTUUID='`/home/cfg/linux/disk/blkid/PARTUUID_root_device` '\t/' '\text4' '\tnoatime' '\t0' '\t1' >> /etc/fstab
#fi

#grep -E "^GRUB_CMDLINE_LINUX=\"net.ifnames=0 rootflags=noatime\"" /etc/default/grub || { echo "GRUB_CMDLINE_LINUX=\"net.ifnames=0 rootflags=noatime\"" >> /etc/default/grub ; }

install_pkg dev-util/strace
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

add_accept_keyword "sys-fs/zfs-9999"
add_accept_keyword "sys-fs/zfs-kmod-9999"
echo -e "#<fs>\t<mountpoint>\t<type>\t<opts>\t<dump/pass>" > /etc/fstab # create empty fstab
#ln -sf /proc/self/mounts /etc/mtab

#grub-install --compress=no --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot --removable --recheck --no-rs-codes "${boot_device}" || exit 1
#grub-install --compress=no --target=i386-pc --boot-directory=/boot --recheck --no-rs-codes "${boot_device}" || exit 1

ln -s /home/cfg/sysskel/etc/skel/bin /root/bin

install_pkg gradm #required for gentoo-hardened RBAC
echo "sys-apps/util-linux static-libs" > /etc/portage/package.use/util-linux    # required for genkernel
echo "sys-kernel/linux-firmware linux-fw-redistributable no-source-code" >> /etc/portage/package.license
install_pkg genkernel
/home/cfg/_myapps/sendgentoo/sendgentoo/kernel_recompile.sh --no-check-boot || exit 1
cat /home/cfg/sysskel/etc/fstab.custom >> /etc/fstab

rc-update add zfs-mount boot # dont exit if this fails
install_pkg dhcpcd  # not in stage3

#grep -E "^config_eth0=\"${ip}/24\"" /etc/conf.d/net || echo "config_eth0=\"${ip}/24\"" >> /etc/conf.d/net
ln -rs /etc/init.d/net.lo /etc/init.d/net.eth0
rc-update add net.eth0 default

mkdir /mnt/t420s_256GB_samsung_ssd_S2R5NX0J707260P
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

rm -f /etc/portage/package.mask
mkdir /etc/portage/package.mask
echo ">net-misc/unison-2.48.4" > /etc/portage/package.mask/unison
install_pkg unison
#ln -s /usr/bin/unison-2.48 /usr/bin/unison
eselect unison list #todo


#echo "=dev-libs/openssl-1.1.1a" > /etc/portage/package.unmask
install_pkg tmux
install_pkg app-portage/repoman
install_pkg vim
install_pkg www-client/links
install_pkg dev-db/redis  # later on, fix_cfg_perms will try to use the redis:redis user
install_pkg sudo
install_pkg app-text/tree
install_pkg sys-fs/safecopy
install_pkg lsof
install_pkg lshw
install_pkg pydf
install_pkg app-portage/gentoolkit #equery
install_pkg sys-process/htop
install_pkg ddrescue
#install_pkg sys-process/cronie  # done in postreboot set
install_pkg net-dns/bind-tools
install_pkg app-admin/sysstat   #mpstat
install_pkg wpa_supplicant
install_pkg sys-apps/sg3_utils
install_pkg dev-util/fatrace
install_pkg sys-apps/smartmontools
rc-update add smartd default
install_pkg sys-fs/multipath-tools
install_pkg net-fs/nfs-utils
install_pkg sys-power/powertop
install_pkg sys-power/upower
rc-update add dbus default

install_pkg dev-util/ccache
mkdir -p /var/cache/ccache
chown root:portage /var/cache/ccache
chmod 2775 /var/cache/ccache

grep -E "^PermitRootLogin yes" /etc/ssh/sshd_config || echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
#rc-update add sshd default

install_pkg app-eselect/eselect-repository
mkdir /etc/portage/repos.conf
for line in `cat /etc/portage/proxy.conf | tr -d '"'`;
do
    export "${line}"
done
eselect repository add jakeogh git https://github.com/jakeogh/jakeogh  #ignores http_proxy
#git config --global http.proxy http://192.168.222.100:8888
emaint sync -r jakeogh
#install_pkg layman
#layman -o "https://raw.githubusercontent.com/jakeogh/jakeogh/master/jakeogh.xml" -f -a jakeogh
#layman -S # update layman trees

# must be done after overlay is installed
#add_accept_keyword "dev-python/kcl-9999"
#add_accept_keyword "dev-python/icecream-9999"
#emerge kcl -1
add_accept_keyword "dev-python/replace-text-9999"
add_accept_keyword "dev-python/icecream-9999"  # dep
add_accept_keyword "dev-python/executing-9999"  # dep
add_accept_keyword "dev-python/asttokens-9999"  # dep
#install_pkg replace-text
emerge replace-text

export LANG="en_US.UTF8"  # to make click happy
grep noclear /etc/inittab || \
    { replace-text "c1:12345:respawn:/sbin/agetty 38400 tty1 linux" "c1:12345:respawn:/sbin/agetty 38400 tty1 linux --noclear" /etc/inittab || exit 1 ; }
install_pkg sys-apps/moreutils # need sponge for the next command
grep "c7:2345:respawn:/sbin/agetty 38400 tty7 linux" /etc/inittab || { cat /etc/inittab | /home/cfg/text/insert_line_after_match "c6:2345:respawn:/sbin/agetty 38400 tty6 linux" "c7:2345:respawn:/sbin/agetty 38400 tty7 linux" | sponge /etc/inittab ; }

# nope, need stuff unmasked....
# make sendgentoo deps happy
#echo "dev-lang/python sqlite" >> /etc/portage/package.use/python || exit 1
#echo "media-libs/gd fontconfig jpeg png truetype" >> /etc/portage/package.use/python || exit 1
#grep sendgentoo /etc/portage/package.accept_keywords || exit 1
#install_pkg sendgentoo --autounmask=y # must be done after jakeogh overlay

# this wont work until symlink tree happens
#install_pkg @sound
#rc-update add alsasound boot
#rc-update add acpid boot

install_pkg net-print/cups
install_pkg net-print/foomatic-db
gpasswd -a root lp
gpasswd -a user lp
gpasswd -a root lpadmin
gpasswd -a user lpadmin

echo "$(date) $0 complete" | tee -a /install_status

