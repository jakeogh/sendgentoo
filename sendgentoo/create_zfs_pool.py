#!/usr/bin/env python3

import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.command import run_command
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
@click.option('--alt-root', is_flag=False, required=False, type=str)
def create_zfs_pool(devices, force, raid, raid_group_size, pool_name, mount_point, alt_root):
    eprint("make_zfs_filesystem_on_devices()")

    # https://raw.githubusercontent.com/ryao/zfs-overlay/master/zfs-install
    run_command("modprobe zfs || exit 1")

    for device in devices:
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device)
        assert not device[-1].isdigit()

    assert raid_group_size >= 1
    assert len(devices) >= raid_group_size

    device_string = ''
    if len(devices) == 1:
        assert raid == 'disk'
        device_string = devices[0]

    if len(devices) > 1:
        assert raid == 'mirror'
        assert len(devices) % 2 == 0
        assert raid_group_size >= 2

    if len(devices) == 2:
        assert raid == 'mirror'
        device_string = "mirror " + devices[0] + ' ' + devices[1]

    if len(devices) > 2:
        if raid_group_size == 2: # striped mirror raid10
            for pair in grouper(devices, 2):
                device_string = device_string + "mirror " + pair[0] + ' ' + pair[1] + ' '
                eprint("device_string:", device_string)
        elif raid_group_size == 4:
            for quad in grouper(devices, 4):
                device_string = device_string + "mirror " + quad[0] + ' ' + quad[1] + ' ' + quad[2] + ' ' + quad[3] + ' '
                eprint("device_string:", device_string)
        else:
            print("unknown mode")
            quit(1)

    assert device_string != ''

    assert len(pool_name) > 2

    if alt_root:
        alt_root = '-R ' + alt_root
    else:
        alt_root = ''

    #-o cachefile='/tmp/zpool.cache'\

    command = "zpool create"
    command += " -o feature@async_destroy=enabled"       # default   # Destroy filesystems asynchronously.
    command += " -o feature@empty_bpobj=enabled"         # default   # Snapshots use less space.
    command += " -o feature@lz4_compress=enabled"        # default   # (independent of the zfs compression flag)
    command += " -o feature@spacemap_histogram=enabled"  # default   # Spacemaps maintain space histograms.
    command += " -o feature@extensible_dataset=enabled"  # default   # Enhanced dataset functionality.
    command += " -o feature@bookmarks=enabled"           # default   # "zfs bookmark" command
    command += " -o feature@enabled_txg=enabled"         # default   # Record txg at which a feature is enabled
    command += " -o feature@embedded_data=enabled"       # default   # Blocks which compress very well use even less space.
    command += " -o feature@large_dnode=enabled"         # default   # Variable on-disk size of dnodes.
    command += " -o feature@large_blocks=enabled"        # default   # Support for blocks larger than 128KB.
    command += " -O atime=off"                           #           # (dont write when reading)
    command += " -O compression=lz4"                     #           # (better than lzjb)
    command += " -O copies=1"                            #
    command += " -O xattr=off"                           #           # (sa is better than on)
    command += " -O sharesmb=off"                        #
    command += " -O sharenfs=off"                        #
    command += " -O checksum=fletcher4"                  # default
    command += " -O dedup=off"                           # default
    command += " -O utf8only=off"                        # default
    command += " -m " + mount_point + ' '
    command += alt_root + ' ' + pool_name + ' ' + device_string

    print(command)
    #run_command(command)

