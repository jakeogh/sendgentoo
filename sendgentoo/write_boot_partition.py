#!/usr/bin/env python3


import sys
from pathlib import Path

import click
from blocktool import add_partition_number_to_device
from blocktool import device_is_not_a_partition
from blocktool import warn
from mounttool import block_special_path_is_mounted
from pathtool import path_is_block_special
from run_command import run_command


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint


@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--force', is_flag=True, required=False)
@click.option('--verbose', is_flag=True, required=False)
@click.option('--debug', is_flag=True, required=False)
def write_boot_partition(*,
                         device: str,
                         force: bool,
                         verbose: bool,
                         debug: bool,):
    ic('creating boot partition  (for grub config, stage2, vmlinuz) on:', device)
    assert device_is_not_a_partition(device=device, verbose=verbose, debug=debug,)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device, verbose=verbose, debug=debug,)

    if not force:
        warn((device,), verbose=verbose, debug=debug,)

    partition_number = '3'
    partition = add_partition_number_to_device(device=device,
                                               partition_number=partition_number,
                                               verbose=verbose)
    start = "100MiB"
    end = "400MiB"

    run_command("parted -a optimal " + device + " --script -- mkpart primary " + start + ' ' + end, verbose=True)
    run_command("parted  " + device + " --script -- name " + partition_number + " bootfs", verbose=True)
    run_command("mkfs.ext4 " + partition, verbose=True)

