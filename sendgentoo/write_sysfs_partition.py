#!/usr/bin/env python3

# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=C0114  # Missing module docstring (missing-module-docstring)
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
# pylint: disable=C0305  # Trailing newlines editor should fix automatically, pointless warning


import sys
import time
from pathlib import Path
from typing import Tuple
from typing import Union

import click
import sh
from asserttool import ic
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tv
from devicetool import add_partition_number_to_device
from devicetool import path_is_block_special
from eprint import eprint
from mounttool import block_special_path_is_mounted
from run_command import run_command
from warntool import warn
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
@click_add_options(click_global_options)
@click.pass_context
def write_sysfs_partition(ctx,
                          devices: Tuple[Path, ...],
                          filesystem: str,
                          force: bool,
                          exclusive: bool,
                          raid: str,
                          raid_group_size: int,
                          pool_name: str,
                          verbose: Union[bool, int, float],
                          verbose_inf: bool,
                          ):

    tty, verbose = tv(ctx=ctx,
                      verbose=verbose,
                      verbose_inf=verbose_inf,
                      )

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

        run_command("parted -a optimal " + devices[0].as_posix() + " --script -- mkpart primary " + filesystem + ' ' + start + ' ' + end, verbose=verbose)
        run_command("parted  " + devices[0].as_posix() + " --script -- name " + partition_number + " rootfs", verbose=verbose,)
        time.sleep(1)
        sysfs_partition_path = add_partition_number_to_device(device=devices[0],
                                                              partition_number=partition_number,
                                                              verbose=verbose,)
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
        ctx.invoke(write_zfs_root_filesystem_on_devices,
                   ctx=ctx,
                   devices=devices,
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
