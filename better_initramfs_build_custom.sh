cd /
mkdir initrd
cp -ar /bin /initrd/
cp -ar /dev /initrd/
cp -ar /etc /initrd/
cp -ar /home /initrd/
cp -a lib /initrd
cp -ar /lib32 /initrd/
cp -ar /lib64 /initrd/
cp -ar /mnt /initrd/
cp -ar /opt /initrd/
mkdir /initrd/proc
cp -ar /root /initrd/    
cp -ar /run /initrd/
cp -ar /sbin /initrd/
mkdir /initrd/sys

cp -ar tmp /initrd/
cp -ar usr /initrd/
rm -rf /initrd/usr/portage/
cp -ar var /initrd/

find /initrd | cpio --quiet -H newc -o | gzip -9 > custom_initramfs.cpio.gz
