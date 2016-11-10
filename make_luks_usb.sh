#!/bin/bash

# Installs LUKS on a USB drive
# It is strongly recommended that you completely overwrite the device with /dev/urandom before using this script.

argcount=1
usage="usb_device"
test "$#" -eq "${argcount}" || { echo "$0 ${usage}" && exit 1 ; }


usb_device="${1}"
shift


echo
echo "THIS SCRIPT WILL DESTROY ALL DATA ON ${usb_device}"
echo "Do you want to proceed? (you must type YES to proceed)"
read delete_usb_device
if [[ "$delete_usb_device" != "YES" ]]; then
	echo "no changes made - aborted"
	exit 2
fi


usb_device_name=`echo "${usb_device}" | cut -d '/' -f 3`
echo "usb_device_name=${usb_device_name}"

mapper_device="/dev/mapper/luks-${usb_device_name}"
echo "mapper_device=${mapper_device}"


function open_luks_usb_device()
{
	echo "Entering open_luks_usb_device()" >> /dev/stderr

	echo "opening ${usb_device} with command: cryptsetup open ${usb_device} luks-${usb_device_name} --type luks"
	cryptsetup open "${usb_device}" luks-"${usb_device_name}" --type luks || exit 1
	ls /dev/mapper/
}


function encrypt_partition_and_format_usb_device_with_lvm()
{
	echo "entering encrypt_partition_and_format_usb_device_with_lvm()" >> /dev/stderr

#	echo "Overwriting first 130560 bytes (127.5kB) of ${usb_device} with /dev/urandom" >> /dev/stderr
#	dd if=/dev/urandom of="${usb_device}" bs=130560 count=1

	cryptsetup -q --debug --verbose -c twofish-xts-essiv:sha256 --key-size 512 --hash sha512 --use-random --verify-passphrase --iter-time 8000 --timeout 240 luksFormat "${usb_device}" || exit 1
	open_luks_usb_device || exit 1
	echo "Creating GPT table on mapper_device ${mapper_device}" >> /dev/stderr
	parted "${mapper_device}" --script -- mklabel gpt || { echo "Unable to make GPT table on mapper_device ${mapper_device}. Exiting." ; exit 1 ; }

	echo "making pv on ${mapper_device}"
	pvcreate -v "${mapper_device}" || exit 1
	vgcreate -v enc_usb_vg "${mapper_device}" || exit 1

	lvcreate -v -l 100%FREE -n usbfs enc_usb_vg || exit 1

	ls -al /dev/mapper/
	mkfs.ext4 -v /dev/mapper/enc_usb_vg-usbfs || exit 1

}



function mount_luks_usb_device_with_lvm()
{
	mkdir /mnt/enc_usb
	mount /dev/mapper/enc_usb_vg-usbfs /mnt/enc_usb || exit 1
}





encrypt_partition_and_format_usb_device_with_lvm || exit 1
mount_luks_usb_device_with_lvm || exit 1

exit 0
