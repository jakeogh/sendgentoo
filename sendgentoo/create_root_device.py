#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Tuple

import click
from blocktool import destroy_block_device_head_and_tail
from blocktool import path_is_block_special
from blocktool import warn
from blocktool import write_gpt
from mounttool import block_special_path_is_mounted

from .setup_globals import RAID_LIST
from .write_sysfs_partition import write_sysfs_partition


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
    from icecream import icr  # https://github.com/jakeogh/icecream
except ImportError:
    ic = eprint
    icr = eprint


@click.command()
@click.argument('devices',         required=True, nargs=-1)
@click.option('--partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
@click.option('--filesystem',      is_flag=False, required=True, type=click.Choice(['ext4', 'zfs', 'fat32']))
@click.option('--force',           is_flag=True,  required=False)
@click.option('--exclusive',       is_flag=True,  required=False)
@click.option('--raid',            is_flag=False, required=True, type=click.Choice(RAID_LIST))
@click.option('--raid-group-size', is_flag=False, required=True, type=int)
@click.option('--pool-name',       is_flag=False, required=False, type=str)
@click.option('--verbose', is_flag=True,  required=False)
@click.option('--debug', is_flag=True,  required=False)
@click.pass_context
def create_root_device(ctx,
                       devices: Tuple[Path, ...],
                       partition_table: str,
                       filesystem: str,
                       force: bool,
                       exclusive: bool,
                       raid: str,
                       raid_group_size: int,
                       verbose: bool,
                       debug: bool,
                       pool_name: str,
                       ):
    devices = tuple([Path(_device) for _device in devices])

    eprint("installing gentoo on root devices:", ' '.join([_device.as_posix() for _device in devices]), '(' + partition_table + ')', '(' + filesystem + ')', '(', pool_name, ')')
    for device in devices:
        if not device.name.startswith('nvme'):
            assert not device.name[-1].isdigit()
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device, verbose=verbose, debug=debug,)

    #assert os.getcwd() == '/home/cfg/setup/gentoo_installer'
    if not force:
        warn(devices, verbose=verbose, debug=debug,)

    if exclusive:
        if filesystem != 'zfs':
            ctx.invoke(destroy_block_device_head_and_tail,
                       device=device,
                       force=True,
                       verbose=verbose,
                       debug=debug,)
            ctx.invoke(write_gpt,
                       device=device,
                       no_wipe=True,
                       force=force,
                       no_backup=False,
                       verbose=verbose,
                       debug=debug,)  # zfs does this on it's own, feed it a blank disk
    else:
        pass

    if pool_name:
        ctx.invoke(write_sysfs_partition,
                   devices=devices,
                   force=True,
                   exclusive=exclusive,
                   filesystem=filesystem,
                   raid=raid,
                   pool_name=pool_name,
                   raid_group_size=raid_group_size,)
    else:
        ctx.invoke(write_sysfs_partition,
                   devices=devices,
                   force=True,
                   exclusive=exclusive,
                   filesystem=filesystem,
                   raid=raid,
                   raid_group_size=raid_group_size,)

