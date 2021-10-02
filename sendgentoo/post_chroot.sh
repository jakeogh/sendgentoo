#!/bin/bash
set -o nounset

echo -n "$0 args: "
echo -e "$@\n"
argcount=7
usage="stdlib boot_device cflags root_filesystem newpasswd pinebook_overlay kernel"
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
pinebook_overlay="${1}"
shift

echo "pinebook_overlay: ${pinebook_overlay}"

mount | grep "/boot/efi" || exit 1

emerge --sync

mkdir -p /var/db/repos/gentoo

zfs_module_mode="module"
env-update || exit 1
source /etc/profile || exit 1
#export PS1="(chroot) $PS1"

#here down is stuff that might not need to run every time
# ---- begin run once, critical stuff ----

#echo "root:$newpasswd" | chpasswd
passwd -d root
chmod +x /home/cfg/sysskel/etc/local.d/*
#echo "PYTHON_TARGETS=\"python3_6 python3_7\"" >> /etc/portage/make.conf
#echo "PYTHON_SINGLE_TARGET=\"python3_6\"" >> /etc/portage/make.conf
#eselect python set --python3 python3.6 || exit 1
#eselect python set python3.6 || exit 1
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

source /etc/profile

echo "sys-devel/gcc fortran" > /etc/portage/package.use/gcc #otherwise gcc compiles twice
install_pkg gcc
gcc-config latest

#install kernel and update symlink (via use flag)
export KCONFIG_OVERWRITECONFIG=1 # https://www.mail-archive.com/lede-dev@lists.infradead.org/msg07290.html
echo "sys-kernel/${kernel} symlink" > /etc/portage/package.use/"${kernel}"    # required so /usr/src/linux exists
install_pkg sys-kernel/"${kernel}" || exit 1
install_pkg grub || exit 1

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


install_pkg app-eselect/eselect-repository
mkdir /etc/portage/repos.conf

for line in $(cat /etc/portage/proxy.conf | tr -d '"' | tr -d '#');
do
    echo "proxy.conf line: ${line}"
    export "${line}"
    grep -E ^"${line}" /etc/wgetrc || { echo "${line}" >> /etc/wgetrc ; }
done

grep -E "^use_proxy = on" /etc/wgetrc || { echo "use_proxy = on" >> /etc/wgetrc ; }



eselect repository list -i | grep jakeogh || eselect repository add jakeogh git https://github.com/jakeogh/jakeogh  #ignores http_proxy
#git config --global http.proxy http://192.168.222.100:8888
install_pkg dev-vcs/git
emaint sync -r jakeogh  # this needs git

if [ ${pinebook_overlay} = '1' ];
then
    eselect repository list -i | grep pinebookpro-overlay || eselect repository add pinebookpro-overlay git https://github.com/Jannik2099/pinebookpro-overlay.git  #ignores http_proxy
    emerge --sync pinebookpro-overlay
    emerge -u pinebookpro-profile-overrides
fi


#install_pkg layman
#layman -o "https://raw.githubusercontent.com/jakeogh/jakeogh/master/jakeogh.xml" -f -a jakeogh
#layman -S # update layman trees

#eselect repository enable java
#emaint sync -r java

#add_accept_keyword "dev-python/icecream-9999"
#add_accept_keyword "dev-python/run-command-9999"
#add_accept_keyword "dev-python/compile-kernel-9999"
install_pkg_force compile-kernel  # requires jakeogh overlay
compile-kernel --no-check-boot || exit 1
cat /home/cfg/sysskel/etc/fstab.custom >> /etc/fstab

# this can be done until memtest86+ and the kernel are ready
/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot_install_grub.sh "${boot_device}" || exit 1

rc-update add zfs-mount boot # dont exit if this fails
install_pkg dhcpcd  # not in stage3

ln -rs /etc/init.d/net.lo /etc/init.d/net.eth0 || exit 1
rc-update add net.eth0 default

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

#rm -f /etc/portage/package.mask
mkdir /etc/portage/package.mask
install_pkg unison
eselect unison list #todo

perl-cleaner --reallyall
#echo "=dev-libs/openssl-1.1.1a" > /etc/portage/package.unmask
install_pkg app-portage/repoman
install_pkg app-editors/vim
install_pkg www-client/links
install_pkg dev-db/redis  # later on, fix_cfg_perms will try to use the redis:redis user
install_pkg app-admin/sudo
install_pkg app-text/tree
install_pkg sys-fs/safecopy
install_pkg sys-process/lsof
install_pkg sys-apps/lshw
install_pkg app-editors/hexedit
install_pkg sys-process/glances
install_pkg app-admin/pydf
install_pkg sys-fs/ncdu
install_pkg app-portage/gentoolkit #equery
install_pkg sys-process/htop
install_pkg sys-fs/ddrescue
#install_pkg sys-process/cronie  # done in postreboot set
install_pkg net-dns/bind-tools
install_pkg app-admin/sysstat   #mpstat
install_pkg wpa_supplicant
install_pkg sys-apps/sg3_utils
install_pkg dev-util/fatrace
install_pkg sys-apps/smartmontools
rc-update add smartd default
install_pkg sys-fs/multipath-tools
install_pkg sys-apps/usbutils  # lsusb for /etc/local.d/ scripts

install_pkg net-fs/nfs-utils
rc-update add nfs default
install_pkg dev-python/distro  # distro detection in boot scripts

install_pkg net-libs/libnfsidmap  # rpc.idmapd

install_pkg sys-power/powertop
install_pkg sys-power/upower
install_pkg sys-apps/dmidecode
install_pkg app-misc/tmux || exit 1
rc-update add dbus default

install_pkg dev-util/ccache
mkdir -p /var/cache/ccache
chown root:portage /var/cache/ccache
chmod 2775 /var/cache/ccache

install_pkg dev-util/ctags  # so vim/nvim dont complain

ls /etc/ssh/sshd_config -al || exit 1
grep -E "^PermitRootLogin yes" /etc/ssh/sshd_config || echo "PermitRootLogin yes" >> /etc/ssh/sshd_config || exit 1
#rc-update add sshd default

install_pkg_force replace-text

export LANG="en_US.UTF8"  # to make click happy
grep noclear /etc/inittab || \
    { replace-text --match "c1:12345:respawn:/sbin/agetty 38400 tty1 linux" --replacement "c1:12345:respawn:/sbin/agetty 38400 tty1 linux --noclear" /etc/inittab || exit 1 ; }
install_pkg sys-apps/moreutils # need sponge for the next command
grep "c7:2345:respawn:/sbin/agetty 38400 tty7 linux" /etc/inittab || { cat /etc/inittab | /home/cfg/text/insert_line_after_match "c6:2345:respawn:/sbin/agetty 38400 tty6 linux" "c7:2345:respawn:/sbin/agetty 38400 tty7 linux" | sponge /etc/inittab ; }

# this wont work until symlink tree happens
#install_pkg @sound
#rc-update add alsasound boot
#rc-update add acpid boot

echo "$(date) $0 complete" | tee -a /install_status
