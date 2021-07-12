Add the github/jakeogh overlay and then "emerge sendgentoo"

```
Usage: sendgentoo [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  create-filesystem
  create-root-device
  create-zfs-filesystem
  create-zfs-pool
  destroy-block-device
  destroy-block-device-head-and-tail
  install
  luksformat

Usage: sendgentoo install [OPTIONS] [ROOT_DEVICES]...

Options:
  --vm [qemu]
  --vm-ram TEXT
  --boot-device TEXT              [required]
  --boot-device-partition-table [gpt]
  --root-device-partition-table [gpt]
  --boot-filesystem [ext4|zfs]
  --root-filesystem [ext4|zfs|9p]
                                  [required]
  --c-std-lib [glibc|musl|uclibc]
  --arch [alpha|amd64|arm|hppa|ia64|mips|ppc|s390|sh|sparc|x86]
  --raid [disk|mirror|raidz1|raidz2|raidz3|raidz10|raidz50|raidz60]
  --raid-group-size INTEGER RANGE
  --march [native|nocona]         [required]
  --hostname TEXT                 [required]
  --newpasswd TEXT                [required]
  --ip TEXT                       [required]
  --ip-gateway TEXT               [required]
  --force
  --encrypt
  --multilib
  --minimal
  --help                          Show this message and exit.
```

TODO:

https://github.com/fearedbliss/bliss-initramfs

https://github.com/Benni3D/microcoreutils/wiki/User-Mode-Linux
