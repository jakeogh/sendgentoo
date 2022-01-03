#!/usr/bin/env python3


import sys
import time
from pathlib import Path
from typing import Tuple

import click
from clicktool import click_add_options, click_global_options
import sh
from asserttool import eprint
from asserttool import ic
from blocktool import add_partition_number_to_device
from blocktool import path_is_block_special
from blocktool import warn
from mounttool import block_special_path_is_mounted
from run_command import run_command
from zfstool import RAID_LIST
from zfstool import write_zfs_root_filesystem_on_devices


@click.command()
@click.argument('devices', required=True, nargs=-1)
@click.option('--filesystem', is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
@click.option('--force', is_flag=True, required=False)
@click.option('--exclusive', is_flag=True, required=False)
@click.option('--raid', is_flag=False, required=True, type=click.Choice(RAID_LIST))
@click.option('--raid-group-size', is_flag=False, required=True, type=int)
@click.option('--pool-name', is_flag=False, type=str)
@click.option('--verbose',)
@click.option('--debug',)
def write_sysfs_partition(devices: Tuple[Path, ...],
                          filesystem: str,
                          force: bool,
                          exclusive: bool,
                          raid: str,
                          raid_group_size: int,
                          pool_name: str,
                          verbose: int,
                                                    ):

    devices = tuple([Path(_device) for _device in devices])
    ic('creating sysfs partition on:', devices)

    if filesystem == 'zfs':
        assert pool_name

    for device in devices:
        if not device.name.startswith('nvme'):
            assert not device.name[-1].isdigit()
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device, verbose=verbose, )

    if not force:
        warn(devices, verbose=verbose, )

    if filesystem in ['ext4', 'fat32']:
        assert len(devices) == 1
        if exclusive:
            #destroy_block_device_head_and_tail(device=device, force=True) #these are done in create_root_device
            #write_gpt(device)
            partition_number = '1'
            start = "0%"
            end = "100%"
        else:
            partition_number = '3'
            start = "100MiB"
            end = "100%"

        run_command("parted -a optimal " + devices[0].as_posix() + " --script -- mkpart primary " + filesystem + ' ' + start + ' ' + end)
        run_command("parted  " + devices[0].as_posix() + " --script -- name " + partition_number + " rootfs")
        time.sleep(1)
        sysfs_partition_path = add_partition_number_to_device(device=devices[0], partition_number=partition_number)
        if filesystem == 'ext4':
            ext4_command = sh.Command('mkfs.ext4')
            ext4_command(sysfs_partition_path.as_posix(), _out=sys.stdout, _err=sys.stderr)
        elif filesystem == 'fat32':
            mkfs_vfat_command = sh.Command('mkfs.vfat', sysfs_partition_path.as_posix())
            mkfs_vfat_command(_out=sys.stdout, _err=sys.stderr)
        else:
            eprint("unknown filesystem:", filesystem)
            sys.exit(1)

    elif filesystem == 'zfs':
        assert exclusive
        assert False
        write_zfs_root_filesystem_on_devices(devices=devices,
                                             mount_point=None,
                                             force=True,
                                             raid=raid,
                                             raid_group_size=raid_group_size,
                                             pool_name=pool_name,
                                             verbose=verbose,
                                             )
    else:
        eprint("unknown filesystem:", filesystem)
        sys.exit(1)
