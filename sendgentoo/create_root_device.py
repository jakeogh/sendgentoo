#!/usr/bin/env python3

from pathlib import Path

import click
from destroy_block_device import destroy_block_device_head_and_tail
from kcl.deviceops import warn
from kcl.deviceops import write_gpt
from kcl.mountops import block_special_path_is_mounted
from kcl.pathops import path_is_block_special
from kcl.printops import eprint

from .setup_globals import RAID_LIST
from .write_sysfs_partition import write_sysfs_partition


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
                       devices,
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

    eprint("installing gentoo on root devices:", ' '.join(devices), '(' + partition_table + ')', '(' + filesystem + ')', '(', pool_name, ')')
    for device in devices:
        if not Path(device).name.startswith('nvme'):
            assert not device[-1].isdigit()
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device)

    #assert os.getcwd() == '/home/cfg/setup/gentoo_installer'
    if not force:
        warn(devices)

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
                       debug=debug,) #zfs does this on it's own, feed it a blank disk
    else:
        pass

    if pool_name:
        ctx.invoke(write_sysfs_partition, devices=devices, force=True, exclusive=exclusive, filesystem=filesystem, raid=raid, pool_name=pool_name, raid_group_size=raid_group_size)
    else:
        ctx.invoke(write_sysfs_partition, devices=devices, force=True, exclusive=exclusive, filesystem=filesystem, raid=raid, raid_group_size=raid_group_size)


#@click.command()
#@click.argument('devices',         required=True, nargs=-1)
#@click.option('--partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
#@click.option('--filesystem',      is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
#@click.option('--force',           is_flag=True,  required=False)
#@click.option('--exclusive',       is_flag=True,  required=False)
#@click.option('--raid',            is_flag=False, required=True, type=click.Choice(RAID_LIST))
#@click.option('--raid-group-size', is_flag=False, required=True, type=int)
#@click.option('--pool-name',       is_flag=False, required=False, type=str)
#@click.pass_context
#def main(ctx, devices, partition_table, filesystem, force, exclusive, raid, raid_group_size, pool_name):
#    create_root_device(ctx, devices=devices, partition_table=partition_table, filesystem=filesystem, force=force, exclusive=exclusive, raid=raid, raid_group_size=raid_group_size, pool_name=pool_name)
#
#
#if __name__ == '__main__':
#    main()

