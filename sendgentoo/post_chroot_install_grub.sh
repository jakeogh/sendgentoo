#!/bin/bash
set -o nounset
#set -x

echo -n "$0 args: "
echo -e "$@"
echo "UID: ${UID}"
echo -e "\n"
argcount=1
usage="boot_device"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" && exit 1 ; }

source /home/cfg/_myapps/sendgentoo/sendgentoo/utils.sh

boot_device="${1}"
shift

ls "${boot_device}" || exit 1

mount | grep "/boot/efi" || { echo "/boot/efi not mounted. Exiting." ; exit 1 ;}

env-update || exit 1

set +u # disable nounset        # line 22 has an unbound variable: user_id /etc/profile.d/java-config-2.sh
source /etc/profile || exit 1
set -o nounset

install_pkg grub || exit 1

#if [[ "${root_filesystem}" == "zfs" ]];
#then
#    echo "GRUB_PRELOAD_MODULES=\"part_gpt part_msdos zfs\"" >> /etc/default/grub
#   #echo "GRUB_CMDLINE_LINUX_DEFAULT=\"boot=zfs root=ZFS=rpool/ROOT\"" >> /etc/default/grub
#   #echo "GRUB_CMDLINE_LINUX_DEFAULT=\"boot=zfs\"" >> /etc/default/grub
#   #echo "GRUB_DEVICE=\"ZFS=rpool/ROOT/gentoo\"" >> /etc/default/grub
#   # echo "GRUB_DEVICE=\"ZFS=${hostname}/ROOT/gentoo\"" >> /etc/default/grub #this was uncommented, disabled to not use hostname
#else
grep -E "^GRUB_PRELOAD_MODULES=\"part_gpt part_msdos\"" /etc/default/grub || { echo "GRUB_PRELOAD_MODULES=\"part_gpt part_msdos\"" >> /etc/default/grub ; }
root_partition=`/home/cfg/linux/disk/get_root_device`
echo "-------------- root_partition: ${root_partition} ---------------------"
partuuid=`/home/cfg/linux/hardware/disk/blkid/PARTUUID "${root_partition}"`
echo "GRUB_DEVICE partuuid: ${partuuid}"
grep -E "^GRUB_DEVICE=\"PARTUUID=${partuuid}\"" /etc/default/grub || { echo "GRUB_DEVICE=\"PARTUUID=${partuuid}\"" >> /etc/default/grub ; }
echo -e 'PARTUUID='`/home/cfg/linux/disk/blkid/PARTUUID_root_device` '\t/' '\text4' '\tnoatime' '\t0' '\t1' >> /etc/fstab
#fi

#grep -E "^GRUB_CMDLINE_LINUX=\"net.ifnames=0 rootflags=noatime irqpoll\"" /etc/default/grub || { echo "GRUB_CMDLINE_LINUX=\"net.ifnames=0 rootflags=noatime irqpoll\"" >> /etc/default/grub ; }
grep -E "^GRUB_CMDLINE_LINUX=\"net.ifnames=0 rootflags=noatime intel_iommu=off\"" /etc/default/grub || { echo "GRUB_CMDLINE_LINUX=\"net.ifnames=0 rootflags=noatime intel_iommu=off\"" >> /etc/default/grub ; }

ln -sf /proc/self/mounts /etc/mtab

grub-install --compress=no --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot --removable --recheck --no-rs-codes "${boot_device}" || exit 1
grub-install --compress=no --target=i386-pc --boot-directory=/boot --recheck --no-rs-codes "${boot_device}" || exit 1

echo "$(date): $0 complete" | tee -a /install_status

