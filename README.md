1. Download gentoo LiveGUI USB Image https://www.gentoo.org/downloads/
2. Boot into LiveGui
3. Disable "suspend session" in "Energy Saving"
4. Connect to the internet https://wiki.gentoo.org/wiki/Handbook:AMD64/Installation/Networking
5. open terminal
6. `sudo su root`
7. `wget https://raw.githubusercontent.com/jakeogh/sendgentoo/master/install.sh`
8. `chmod +x install.sh`
9. `./intstall.sh`



Add the github/jakeogh overlay and then "emerge sendgentoo"

```
$ sendgentoo
Usage: sendgentoo [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  chroot-gentoo
  compile-kernel
  create-boot-device-for-existing-root
  create-filesystem
  create-root-device
  create-zfs-filesystem
  create-zfs-filesystem-snapshot
  create-zfs-pool
  install
  rsync-cfg
  zfs-check-mountpoints
  zfs-set-sharenfs



$ sendgentoo install --help
Usage: sendgentoo install [OPTIONS] [ROOT_DEVICES]...

Options:
  --vm [qemu]
  --vm-ram INTEGER
  --boot-device TEXT              [required]
  --boot-device-partition-table [gpt]
  --root-device-partition-table [gpt]
  --boot-filesystem [ext4|zfs]
  --root-filesystem [ext4|zfs|9p]
                                  [required]
  --stdlib [glibc|musl|uclibc]
  --arch [alpha|amd64|arm|hppa|ia64|mips|ppc|s390|sh|sparc|x86]
  --raid [disk|mirror|raidz1|raidz2|raidz3|raidz10|raidz50|raidz60]
  --raid-group-size INTEGER RANGE
                                  [1<=x<=2]
  --march [native|nocona]         [required]
  --hostname TEXT                 [required]
  --newpasswd TEXT                [required]
  --ip TEXT                       [required]
  --ip-gateway TEXT               [required]
  --proxy TEXT                    [required]
  --force
  --encrypt
  --multilib
  --minimal
  --verbose
  --debug
  --help                          Show this message and exit.

```

OTHER PARTS:

https://github.com/jakeogh/sendgentoo-stage

https://github.com/jakeogh/sendgentoo-chroot

https://github.com/jakeogh/sendgentoo-post-chroot


TODO:

https://github.com/fearedbliss/bliss-initramfs

https://github.com/Benni3D/microcoreutils/wiki/User-Mode-Linux
