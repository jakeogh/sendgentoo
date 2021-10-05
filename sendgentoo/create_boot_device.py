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


import sys
from pathlib import Path

import click
from blocktool import create_filesystem
from blocktool import destroy_block_device_head_and_tail
from blocktool import device_is_not_a_partition
from blocktool import path_is_block_special
from blocktool import warn
from blocktool import write_efi_partition
from blocktool import write_gpt
from blocktool import write_grub_bios_partition
from mounttool import block_special_path_is_mounted


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint


def create_boot_device(ctx, *,
                       device,
                       partition_table,
                       filesystem,
                       force: bool,
                       verbose: bool,
                       debug: bool,):

    assert device_is_not_a_partition(device=device, verbose=verbose, debug=debug,)

    eprint("installing gpt/grub_bios/efi on boot device:",
           device,
           '(' + partition_table + ')',
           '(' + filesystem + ')',)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device, verbose=verbose, debug=debug,)

    if not force:
        warn((device,), verbose=verbose, debug=debug,)

    # dont do this here, want to be able to let zfs make
    # the gpt and it's partitions before making bios_grub and EFI
    #destroy_block_device_head_and_tail(device=device, force=True)

    if partition_table == 'gpt':
        if filesystem != 'zfs':
            ctx.invoke(destroy_block_device_head_and_tail,
                       device=device,
                       force=force,
                       no_backup=False,
                       verbose=True,
                       debug=debug,)

            ctx.invoke(write_gpt,
                       device=device,
                       no_wipe=True,
                       force=force,
                       no_backup=False,
                       verbose=verbose,
                       debug=debug,) # zfs does this

    if filesystem == 'zfs':
        # 2 if zfs made sda1 and sda9
        ctx.invoke(write_grub_bios_partition,
                   device=device,
                   force=True,
                   start='48s',
                   end='1023s',
                   partition_number='2',
                   verbose=verbose,
                   debug=debug,)
    else:
        ctx.invoke(write_grub_bios_partition,
                   device=device,
                   force=True,
                   start='48s',
                   end='1023s',
                   partition_number='1',
                   verbose=verbose,
                   debug=debug,)

    if filesystem != 'zfs':
        ctx.invoke(write_efi_partition,
                   device=device,
                   force=True,
                   start='1024s',
                   end='18047s',
                   partition_number='2',
                   verbose=verbose,
                   debug=debug,) # this is /dev/sda9 on zfs
        # 100M = (205824-1024)*512
        #ctx.invoke(write_efi_partition,
        #           device=device,
        #           force=True,
        #           start='1024s',
        #           end='205824s',
        #           partition_number='2',
        #           verbose=verbose,
        #           debug=debug,) # this is /dev/sda9 on zfs

    if filesystem == 'zfs':
        assert False
        create_filesystem(device=device + '9',
                          filesystem='fat16',
                          force=True,
                          raw_device=False,
                          verbose=verbose,
                          debug=debug,)

@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--partition-table', is_flag=False, required=True, type=click.Choice(['gpt']), default='gpt')
@click.option('--filesystem', is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']), default='ext4')
@click.option('--force', is_flag=True,  required=False)
@click.pass_context
def main(ctx, device, partition_table, filesystem, force):
    create_boot_device(ctx,
                       device=device,
                       partition_table=partition_table,
                       filesystem=filesystem,
                       force=force,
                       verbose=ctx['verbose'],
                       debug=ctx['debug'],)
