#!/bin/bash

argcount=7
usage="stdlib boot_device hostname cflags root_filesystem newpasswd ip"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" > /dev/stderr && exit 1 ; } #"-ge=>=" "-gt=>" "-le=<=" "-lt=<" "-ne=!="

stdlib="${1}"
boot_device="${2}"
hostname="${3}"
cflags="${4}"
root_filesystem="${5}"
newpasswd="${6}"
ip="${7}"

echo "checking /proc /sys and /dev mounts in prep to chroot"
mount | grep '/mnt/gentoo/proc' || { mount -t proc none /mnt/gentoo/proc || exit 1 ; }
mount | grep '/mnt/gentoo/sys' || { mount --rbind /sys /mnt/gentoo/sys || exit 1 ; }
mount | grep '/mnt/gentoo/dev' || { mount --rbind /dev /mnt/gentoo/dev || exit 1 ; }

echo "bind mounting /usr/portage"
test -d /mnt/gentoo/usr/portage || { mkdir -p /mnt/gentoo/usr/portage || exit 1 ; }
mount | grep '/mnt/gentoo/usr/portage' || { mount --rbind /usr/portage /mnt/gentoo/usr/portage || exit 1 ; }

echo "making /mnt/gentoo/home/cfg"
test -d /mnt/gentoo/home/cfg || { mkdir -p /mnt/gentoo/home/cfg || exit 1 ; }
#mount | grep '/mnt/gentoo/home/cfg' || { mount --rbind /home/cfg /mnt/gentoo/home/cfg || exit 1 ; }

test -d /mnt/gentoo/usr/local/portage || { mkdir -p /mnt/gentoo/usr/local/portage || exit 1 ; }

echo "cp -ar /home/cfg /mnt/gentoo/home/"
#time cp -ar /home/cfg /mnt/gentoo/home/ || exit 1
#time (cd /home && tar --one-file-system -z -c -f --exclude "/home/cfg/_priv" - cfg ) | pv -trabT -B 600M | (cd /mnt/gentoo/home && tar zxpSf - )
cd /home || exit 1
#tar --exclude="_priv" --one-file-system -z -c -f - cfg | pv -trabT -B 600M | tar -C /mnt/gentoo/home -zxpSf - || exit 1

rsync --exclude="_priv" --one-file-system --delete -v -r -z -l --progress /home/cfg /mnt/gentoo/home/ || exit 1

#test -h /mnt/gentoo/boot/vmlinuz || { cp -af /boot/* /mnt/gentoo/boot/ || exit 1 ; }

if [[ "${root_filesystem}" == 'zfs' ]];
then
    mkdir -p /mnt/gentoo/etc/zfs
    cp /etc/zfs/zpool.cache /mnt/gentoo/etc/zfs/zpool.cache
fi

echo "Entering chroot"
env -i HOME=/root TERM=$TERM chroot /mnt/gentoo /bin/bash -l -c "su - -c '/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot.sh ${stdlib} ${boot_device} ${hostname} ${cflags} ${root_filesystem} ${newpasswd} ${ip}'" || { echo "post_chroot.sh exited $?" ; exit 1 ; }

#eclean-pkg -d #remove outdated binary packages before cp #hm, deletes stuff it shouldnt...

umount /mnt/gentoo/usr/portage || exit 1
portage_size=`du -s /usr/portage | cut -f 1`
portage_size_plus_15_pct=`python -c "print(int($portage_size*1.15))"`

mnt_gentoo_free=`/bin/df | egrep "/mnt/gentoo$" | ~/cfg/text/collapse_whitespace | cut -d ' ' -f 4`

if [[ "${mnt_gentoo_free}" -gt "${portage_size_plus_15_pct}" ]];
then
    cp -ar /usr/portage /mnt/gentoo/usr/
    du -sh /mnt/gentoo/usr/portage
    rm -rf /mnt/gentoo/usr/portage/packages  # bad -march
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
