#!/usr/bin/env python3

# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=W0511  # todo is encouraged
# pylint: disable=C0301  # line too long
# pylint: disable=R0902  # too many instance attributes
# pylint: disable=C0302  # too many lines in module
# pylint: disable=C0103  # single letter var names, func name too descriptive
# pylint: disable=R0911  # too many return statements
# pylint: disable=R0912  # too many branches
# pylint: disable=R0915  # too many statements
# pylint: disable=R0913  # too many arguments
# pylint: disable=R1702  # too many nested blocks
# pylint: disable=R0914  # too many local variables
# pylint: disable=R0903  # too few public methods
# pylint: disable=E1101  # no member for base
# pylint: disable=W0201  # attribute defined outside __init__
# pylint: disable=R0916  # Too many boolean expressions in if statement


import click
from icecream import ic
from kcl.pathops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.commandops import run_command
from kcl.iterops import grouper
from kcl.printops import eprint
from .setup_globals import RAID_LIST


@click.command()
@click.argument('devices', required=True, nargs=-1)
@click.option('--force', is_flag=True, required=False)
@click.option('--raid', is_flag=False, required=True, type=click.Choice(RAID_LIST))
@click.option('--raid-group-size', is_flag=False, required=True, type=int)
@click.option('--pool-name', is_flag=False, required=True, type=str)
@click.option('--mount-point', is_flag=False, required=True, type=str)
@click.option('--verbose', is_flag=True)
def write_zfs_root_filesystem_on_devices(devices,
                                         force,
                                         raid,
                                         raid_group_size,
                                         pool_name,
                                         mount_point,
                                         verbose):

    if verbose:
        ic()

    # https://raw.githubusercontent.com/ryao/zfs-overlay/master/zfs-install
    run_command("modprobe zfs || exit 1")

    for device in devices:
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device)
        if not Path(device).name.startswith('nvme'):
            assert not device[-1].isdigit()

    #assert raid_group_size >= 2
    assert len(devices) >= raid_group_size

    device_string = ''
    if len(devices) == 1:
        assert raid == 'disk'
        device_string = devices[0]

    if len(devices) > 1:
        assert raid == 'mirror'
        assert len(devices) % 2 == 0

    if len(devices) == 2:
        assert raid == 'mirror'
        device_string = "mirror " + devices[0] + ' ' + devices[1]

    # striped mirror raid10
    if len(devices) > 2:
        for pair in grouper(devices, raid_group_size):
            device_string = device_string + "mirror " + pair[0] + ' ' + pair[1] + ' '
            eprint("device_string:", device_string)
    assert device_string != ''

    assert len(pool_name) > 2

    zpool_command = """
    zpool create \
    -f \
    -o feature@async_destroy=enabled \
    -o feature@empty_bpobj=enabled \
    -o feature@lz4_compress=enabled \
    -o feature@spacemap_histogram=enabled \
    -o feature@extensible_dataset=enabled \
    -o feature@bookmarks=enabled \
    -o feature@enabled_txg=enabled \
    -o feature@embedded_data=enabled \
    -o cachefile='/tmp/zpool.cache'\
    -O atime=off \
    -O compression=lz4 \
    -O copies=1 \
    -O xattr=sa \
    -O sharesmb=off \
    -O sharenfs=off \
    -O checksum=fletcher4 \
    -O dedup=off \
    -O utf8only=off \
    -m none \
    -R """ + mount_point + ' ' + pool_name + ' ' + device_string

#    zpool_command = """
#    zpool create \
#    -f \
#    -o feature@async_destroy=enabled \
#    -o feature@empty_bpobj=enabled \
#    -o feature@lz4_compress=enabled \
#    -o feature@spacemap_histogram=enabled \
#    -o feature@enabled_txg=enabled \
#    -o feature@extensible_dataset=enabled \
#    -o feature@embedded_data=enabled \
#    -o feature@bookmarks=enabled \
#    -o cachefile='/tmp/zpool.cache'\
#    -O atime=off \
#    -O compression=lz4 \
#    -O xattr=sa \
#    -O sharesmb=off \
#    -O sharenfs=off \
#    -O checksum=sha256 \
#    -O dedup=off \
#    -m none \
#    -R /mnt/gentoo \
#    rpool """ + ' '.join(devices)

    run_command(zpool_command, verbose=True)

    # Workaround 0.6.4 regression
    #run_command("zfs umount /mnt/gentoo/rpool")
    #run_command("rmdir /mnt/gentoo/rpool")

    # Create rootfs
    run_command("zfs create -o mountpoint=none " + pool_name + "/ROOT", verbose=True)
    run_command("zfs create -o mountpoint=/ " + pool_name + "/ROOT/gentoo", verbose=True)

    # Create home directories
    #zfs create -o mountpoint=/home rpool/HOME
    #zfs create -o mountpoint=/root rpool/HOME/root

    # Create portage directories
    #zfs create -o mountpoint=none -o setuid=off rpool/GENTOO
    #zfs create -o mountpoint=/usr/portage -o atime=off rpool/GENTOO/portage
    #zfs create -o mountpoint=/usr/portage/distfiles rpool/GENTOO/distfiles

    # Create portage build directory
    #run_command("zfs create -o mountpoint=/var/tmp/portage -o compression=lz4 -o sync=disabled rpool/GENTOO/build-dir")

    # Create optional packages directory
    #zfs create -o mountpoint=/usr/portage/packages rpool/GENTOO/packages

    # Create optional ccache directory
    #zfs create -o mountpoint=/var/tmp/ccache -o compression=lz4 rpool/GENTOO/ccache

    # Set bootfs
    run_command("zpool set bootfs=" + pool_name + "/ROOT/gentoo " + pool_name, verbose=True)

    # Copy zpool.cache into chroot
    run_command("mkdir -p /mnt/gentoo/etc/zfs", verbose=True)
    run_command("cp /tmp/zpool.cache /mnt/gentoo/etc/zfs/zpool.cache", verbose=True)

    #print("done making zfs filesystem, here's what is mounted:")
    #run_command('mount')

