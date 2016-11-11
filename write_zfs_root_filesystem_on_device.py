#!/usr/bin/env python3
import os
import sys
import click
import time
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.command import run_command

def write_zfs_root_filesystem_on_device(device, force):
    print("make_zfs_filesystem_on_device()")

    # https://raw.githubusercontent.com/ryao/zfs-overlay/master/zfs-install
    run_command("modprobe zfs || exit 1")
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    assert not device[-1].isdigit()

    zpool_command = """
    zpool create        \
    -f                  \
    -o feature@async_destroy=enabled \
    -o feature@empty_bpobj=enabled \
    -o feature@lz4_compress=enabled \
    -o feature@spacemap_histogram=enabled \
    -o feature@enabled_txg=enabled \
    -o feature@extensible_dataset=enabled \
    -o feature@embedded_data=enabled \
    -o feature@bookmarks=enabled \
    -o cachefile='/tmp/zpool.cache'     \
    -O atime=off        \
    -O compression=lz4  \
    -O xattr=sa         \
    -O sharesmb=off     \
    -O sharenfs=off     \
    -O checksum=sha256  \
    -O dedup=off        \
    -m none   \
    -R /mnt/gentoo  \
    rpool \"${device}\" """

    # Workaround 0.6.4 regression
    run_command("zfs umount /mnt/gentoo/rpool")
    run_command("rmdir /mnt/gentoo/rpool")

    # Create rootfs
    run_command("zfs create -o mountpoint=none rpool/ROOT")
    run_command("zfs create -o mountpoint=/ rpool/ROOT/gentoo")

    # Create home directories
    #zfs create -o mountpoint=/home rpool/HOME
    #zfs create -o mountpoint=/root rpool/HOME/root

    # Create portage directories
    #zfs create -o mountpoint=none -o setuid=off rpool/GENTOO
    #zfs create -o mountpoint=/usr/portage -o atime=off rpool/GENTOO/portage
    #zfs create -o mountpoint=/usr/portage/distfiles rpool/GENTOO/distfiles

    # Create portage build directory
    run_command("zfs create -o mountpoint=/var/tmp/portage -o compression=lz4 -o sync=disabled rpool/GENTOO/build-dir")

    # Create optional packages directory
    #zfs create -o mountpoint=/usr/portage/packages rpool/GENTOO/packages

    # Create optional ccache directory
    #zfs create -o mountpoint=/var/tmp/ccache -o compression=lz4 rpool/GENTOO/ccache

    # Set bootfs
    run_command("zpool set bootfs=rpool/ROOT/gentoo rpool")

    # Copy zpool.cache into chroot
    run_command("mkdir -p /mnt/gentoo/etc/zfs")
    run_command("cp /tmp/zpool.cache /mnt/gentoo/etc/zfs/zpool.cache")

    print("done making zfs filesystem, here's what is mounted:")
    run_command(mount)


@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--force',  is_flag=True,  required=False)
def main(device, force):
    write_zfs_root_filesystem_on_device(device=device, force=force)

if __name__ == '__main__':
    main()
