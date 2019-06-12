#!/bin/bash

set -o nounset

argcount=9
usage="stdlib boot_device hostname cflags root_filesystem newpasswd ip vm destination"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

stdlib="${1}"
boot_device="${2}"
hostname="${3}"
cflags="${4}"
root_filesystem="${5}"
newpasswd="${6}"
ip="${7}"
vm="${8}"
destination="${9}"

if [[ "${vm}" == "qemu" ]];
then
    mount --bind "${destination}"{,-chroot} || { echo "${destination} ${destination}-chroot" ; exit 1 ; }
fi

grep -E "^config_eth0=\"${ip}/24\"" "${destination}/etc/conf.d/net" || echo "config_eth0=\"${ip}/24\"" >> "${destination}/etc/conf.d/net"

echo "hostname=\"${hostname}\"" > "${destination}/etc/conf.d/hostname"

echo "checking /proc /sys and /dev mounts in prep to chroot"
mount | grep "${destination}/proc" || { mount -t proc none "${destination}/proc" || exit 1 ; }
mount | grep "${destination}/sys" || { mount --rbind /sys "${destination}/sys" || exit 1 ; }
mount | grep "${destination}/dev" || { mount --rbind /dev "${destination}/dev" || exit 1 ; }

echo "bind mounting /usr/portage"
test -d "${destination}/usr/portage" || { mkdir -p "${destination}/usr/portage" || exit 1 ; }
mount | grep "${destination}/usr/portage" || { mount --rbind /usr/portage "${destination}/usr/portage" || exit 1 ; }

echo "making ${destination}/home/cfg"
test -d "${destination}/home/cfg" || { mkdir -p "${destination}/home/cfg" || exit 1 ; }

test -d "${destination}/usr/local/portage" || { mkdir -p "${destination}/usr/local/portage" || exit 1 ; }

echo "cp -ar /home/cfg ${destination}/home/"
#time cp -ar /home/cfg /mnt/gentoo/home/ || exit 1
#time (cd /home && tar --one-file-system -z -c -f --exclude "/home/cfg/_priv" - cfg ) | pv -trabT -B 600M | (cd /mnt/gentoo/home && tar zxpSf - )
cd /home || exit 1
#tar --exclude="_priv" --one-file-system -z -c -f - cfg | pv -trabT -B 600M | tar -C /mnt/gentoo/home -zxpSf - || exit 1

rsync --exclude="_priv" --one-file-system --delete -v -r -z -l --progress /home/cfg "${destination}/home/" || exit 1

if [[ "${root_filesystem}" == 'zfs' ]];
then
    mkdir -p "${destination}/etc/zfs"
    cp /etc/zfs/zpool.cache "${destination}/etc/zfs/zpool.cache"
fi

echo "Entering chroot"
env -i HOME=/root TERM=$TERM chroot "${destination}" /bin/bash -l -c "su - -c '/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot.sh ${stdlib} ${boot_device} ${cflags} ${root_filesystem} ${newpasswd}'" || { echo "post_chroot.sh exited $?" ; exit 1 ; }

umount "${destination}/usr/portage" || exit 1
portage_size=`du -s /usr/portage | cut -f 1`
portage_size_plus_15_pct=`python -c "print(int($portage_size*1.15))"`

mnt_gentoo_free=`/bin/df | egrep ""${destination}$" | ~/cfg/text/collapse_whitespace | cut -d ' ' -f 4`

if [[ "${mnt_gentoo_free}" -gt "${portage_size_plus_15_pct}" ]];
then
    cp -ar /usr/portage "${destination}/usr/"
    du -sh "${destination}/usr/portage"
    rm -rf "${destination}/usr/portage/packages"  # bad -march
else
    echo "mnt_gentoo_free: ${mnt_gentoo_free}"
    echo "portage_size_plus_15_pct: ${portage_size_plus_15_pct}"
    echo "skipping /usr/portage copy"
fi

/home/cfg/_myapps/sendgentoo/sendgentoo/umount_mnt_gentoo.sh
/home/cfg/_myapps/sendgentoo/sendgentoo/umount_mnt_gentoo.sh
/home/cfg/_myapps/sendgentoo/sendgentoo/umount_mnt_gentoo.sh
/home/cfg/_myapps/sendgentoo/sendgentoo/umount_mnt_gentoo.sh

/home/cfg/_myapps/sendgentoo/sendgentoo/gpart_make_hybrid_mbr.sh "${boot_device}" #would be nice to do this earlier

echo "gentoo install complete! might need to fix grub.cfg"
