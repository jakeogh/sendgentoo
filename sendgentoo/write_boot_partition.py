#!/usr/bin/env python3


from pathlib import Path

import click
from icecream import ic
from kcl.commandops import run_command
from kcl.deviceops import device_is_not_a_partition
from kcl.deviceops import warn
from kcl.mountops import block_special_path_is_mounted
from kcl.pathops import path_is_block_special
from kcl.printops import eprint


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
    assert not block_special_path_is_mounted(device)

    if not force:
        warn((device,))

    partition_number = '3'
    start = "100MiB"
    end = "400MiB"

    run_command("parted -a optimal " + device + " --script -- mkpart primary " + start + ' ' + end)
    run_command("parted  " + device + " --script -- name " + partition_number + " bootfs")
    run_command("mkfs.ext4 " + device + partition_number)

